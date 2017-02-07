# import lauescript
# from lauescript.laueio import loader
# from lauescript.cryst.iterators import iter_atom_pairs
from lauescript.cryst.transformations import frac2cart
from lauescript.types.adp import ADPDataError
from floppy.node import Node, abstractNode, Input, Output, Tag, ForLoop
from floppy.FloppyTypes import Atom
import subprocess
import os

@abstractNode
class CrystNode(Node):
    Tag('Crystallography')


class ReadAtoms(CrystNode):
    Input('FileName', str)
    Output('Atoms', Atom, list=True)

    def run(self):
        super(ReadAtoms, self).run()
        from lauescript.laueio.loader import Loader
        loader = Loader()
        loader.create(self._FileName)
        print('1')
        mol = loader.load('quickloadedMolecule')
        print('2')
        self._Atoms(mol.atoms)


class BreakAtom(CrystNode):
    Input('Atom', Atom)
    Output('Name', str)
    Output('Element', str)
    Output('frac', float, list=True)
    Output('cart', float, list=True)
    Output('ADP',float, list=True)
    Output('ADP_Flag', str)
    Output('Cell',float, list=True)

    def run(self):
        super(BreakAtom, self).run()
        atom = self._Atom
        # print(atom, atom.molecule.get_cell(degree=True))
        self._Name(atom.get_name())
        self._Element(atom.get_element())
        self._frac(atom.get_frac())
        self._cart(atom.get_cart())
        try:
            adp = atom.adp['cart_meas']
        except ADPDataError:
            adp = [0, 0, 0, 0, 0, 0]
        self._ADP(adp)
        self._ADP_Flag(atom.adp['flag'])
        self._Cell(atom.molecule.get_cell(degree=True))

    # def check(self):
    #     for inp in self.inputs.values():
    #         print(inp.value)
    #     return super(BreakAtom, self).check()


class Frac2Cart(CrystNode):
    Input('Position', float, list=True)
    Input('Cell', float, list=True)
    Output('Cart', float, list=True)

    def run(self):
        super(Frac2Cart, self).run()
        self._Cart(frac2cart(self._Position, self._Cell))


class SelectAtom(CrystNode):
    Input('AtomList', Atom, list=True)
    Input('AtomName', str)
    Output('Atom', Atom)

    def run(self):
        super(SelectAtom, self).run()
        name = self._AtomName
        self._Atom([atom for atom in self._AtomList if atom.get_name() == name][0])


class PDB2INS(CrystNode):
    Input('FileName', str)
    Input('Wavelength', float)
    Input('HKLF', int)
    Input('CELL', str)
    Input('SpaceGroup', str)
    Input('ANIS', bool)
    Input('MakeHKL', bool)
    Input('REDO', bool)
    Input('Z', int)
    Output('INS', str)
    Output('HKL', str)
    Output('PDB', str)

    def __init__(self, *args, **kwargs):
        super(PDB2INS, self).__init__(*args, **kwargs)
        self.stdout = ''

    def check(self):
        x = self.inputs['FileName'].isAvailable()
        return x

    def run(self):
        super(PDB2INS, self).run()
        opt =  ('pdb2ins',
                self._FileName,
                '-i',
                '-o __pdb2ins__.ins',
                ' -w '+str(self._Wavelength) if self._Wavelength else '',
                ' -h '+str(self._HKLF) if self._HKLF else '',
                ' -c '+str(self._CELL) if self._CELL else '',
                ' -s '+str(self._SpaceGroup) if self._SpaceGroup else '',
                ' -a ' if self._ANIS else '-a',
                ' -b ' if self._MakeHKL else '-b',
                ' -r ' if self._REDO else '',
                ' -z ' + str(self._Z) if self._Z else '',
                (' -d '+ self._FileName+'.sf') if not '@' in self._FileName else '')
        opt = ' '.join(opt)
        print(opt)
        # opt = [o for o in ' '.join(opt).split(' ') if o]
        # print(opt)
        self.p = subprocess.Popen(opt, shell=True, stdout=subprocess.PIPE)
        self.stdout = ''
        while True:
            line = self.p.stdout.readline()
            if not line:
                break
            self.stdout += str(line)[1:]
        # print('ran')
        self._INS(open('__pdb2ins__.ins', 'r').read())
        try:
            self._HKL(open('__pdb2ins__.hkl', 'r').read())
        except IOError:
            try:
                self._HKL(open('{}.hkl'.format(self._FileName), 'r').read())
            except IOError:
                self._HKL('')
        try:
            self._PDB(open('__pdb2ins__.pdb', 'r').read())
        except IOError:
            self._PDB(open('{}.pdb'.format(self._FileName), 'r').read())
        for file in os.listdir():
            if file.startswith('__pdb2ins__'):
                os.remove(file)

    def report(self):
        r = super(PDB2INS, self).report()
        r['stdout'] = self.stdout
        r['template'] = 'ProgramTemplate'
        return r


class BreakPDB(CrystNode):
    Input('PDB', str)
    Output('Code', str)
    Output('R1', float)

    def run(self):
        for line in self._PDB.splitlines():
            if line.startswith('REMARK   3   R VALUE') and '(WORKING SET)' in line:
                line = [i for i in line[:-1].split() if i]
                r1 = line[-1]
            elif line.startswith('HEADER'):
                line = [i for i in line[:-1].split() if i]
                code = line[-1]
        self._Code(code)
        self._R1(r1)


class ForEachAtomPair(ForLoop):
    Input('Start', Atom, list=True)
    Output('Atom1', Atom)
    Output('Atom2', Atom)

    # def __init__(self, *args, **kwargs):
    #     super(ForEachAtomPair, self).__init__(*args, **kwargs)

    def run(self):
        atoms = self._Start
        if self.fresh:
            self.x = 0
            self.y = 1
            self.end = len(atoms)-1
        self.fresh = False
        self._Atom1(atoms[self.x])
        self._Atom2(atoms[self.y])
        self.y += 1
        if self.y >= self.end:
            self.x += 1
            self.y = self.x+1
        if self.x >= self.end:
            self._Final(self._Start)
            self.done = True
