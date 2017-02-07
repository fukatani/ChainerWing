import floppy.quickPlot as qp

class ColorDict(object):

    def __init__(self, d):
        self.dict = d


    def __getitem__(self, item):
        try:
            return self.dict[item]
        except KeyError:
            return 'rgb(255,255,255'

TEMPLATES = {}
TYPECOLORS = ColorDict({'str': 'rgb(255, 190, 0)',
              'int': 'rgb(0, 115, 130)',
              'float': 'rgb(0, 200, 0)',
              'object': 'rgb(190, 190, 190)',
              'bool': 'rgb(190, 0, 0)',
              })


class TemplateElement(object):
    pass


class IOElement(TemplateElement):
    def __call__(self, data, cache, fileBase, width):
        s = '''
        <style>
        body{{
  background: #606060;
}}

#pricing-table {{
	text-align: center;
	background: #707070;
	width: {width}px; /* total computed width = 222 x 3 + 226 */
}}

#pricing-table .plan {{
	font: 12px 'Lucida Sans', 'trebuchet MS', Arial, Helvetica;
	background: #707070;
	color: #333;
	padding: 20px;
	width: {ewidth}px; /* plan width = 180 + 20 + 20 + 1 + 1 = 222px */
	float: left;
	position: relative;
}}



#pricing-table .plan:nth-child(1) {{
	border-radius: 5px 0 0 5px;
}}

#pricing-table .plan:nth-child(2) {{
	border-radius: 0 5px 5px 0;
}}

/* --------------- */

#pricing-table h3 {{
	font-size: 20px;
	color: #eee;
	font-weight: normal;
	padding: 15px;
	height: 35px;
	margin: -20px -20px 50px -20px;
	background-color: #505050;
}}



#pricing-table .plan:nth-child(1) h3 {{
	border-radius: 5px 0 0 0;
}}

#pricing-table .plan:nth-child(2) h3 {{
	border-radius: 0 5px 0 0;
}}

#pricing-table h3 span {{
	display: block;
	font: bold 15px/30px Helvetica, sans-serif;
	color: #eee;
	background: #707070;
	border: 5px solid #606060;
	height: 30px;
	width: 75px;
	margin: 10px auto -65px;
	border-radius: 100px;
	box-shadow: 0 5px 20px #505050 inset, 0 3px 0 #707070 inset;
}}

/* --------------- */

#pricing-table ul {{
	margin: 20px 0 0 0;
	padding: 0;
	list-style: none;
}}

#pricing-table li {{
	border-top: 1px solid #aaa;
	padding: 10px 0;
}}

/* --------------- */

.clear:before, .clear:after {{
  content:"";
  display:table
}}

.clear:after {{
  clear:both
}}

.clear {{
  zoom:1
}}
        </style>
    <div id="pricing-table" class="clear">
        <div class="plan">
            <h3>Input<span>{ready}</span></h3>
            <ul>
                {inputs}
            </ul>
        </div>
        <div class="plan">
            <h3>Output<span>Waiting</span></h3>
            <ul>
                {outputs}

            </ul>
        </div>

    </div>
        '''.format(width=width,
                   ready=data['ready'],
                   ewidth=(width - 80) / 2,
                   inputs='\n'.join(['<li><b><span style="color:{}">{}</span></b>  {}</li>'.format(TYPECOLORS[
                                                                                                       varType],
                                                                                                   name,
                                                                                                   value) for
                                     name, varType, value in data['inputs']]),
                   outputs='\n'.join(['<li><b><span style="color:{}">{}</span></b>  {}</li>'.format(TYPECOLORS[
                                                                                                       varType],
                                                                                                   name,
                                                                                                   value) for
                                     name, varType, value in data['outputs']]))
        return s


class PlotElement(TemplateElement):
    def __init__(self):
        self.document = qp.LinePlot(430, 320, color='#707070')
        self.document.setTicks(2, 4)
        #self.document.addFrame()

    def __call__(self, data, cache, fileBase, width):
        self.document.setWidth(width)
        for x, y in data['points']:
            if not type(y) == list:
                y = [y]
            self.document.addPoint(x, y)
        try:
            self.document.plot()
        except ValueError:
            return ''
        else:
            return str(self.document)

class StdoutElement(TemplateElement):
    def __call__(self, data, cache, fileBase, width):
        return data['stdout'].replace('\\n', '<br>')


class MetaTemplate(type):
    def __new__(cls, name, bases, classdict):
        result = type.__new__(cls, name, bases, classdict)
        # result.__dict__['Input'] = result._addInput
        TEMPLATES[name] = result
        return result


class Template(object, metaclass=MetaTemplate):
    ELEMENTS = []

    def __init__(self):
        self.elements = [element() for element in self.ELEMENTS]

    def __call__(self, data, cache, fileBase, width):
        return '''
<HTML>

    <BODY bgcolor="#606060">
        <P>This is an abstract Base Template.
        Please don't use me.</P>
    </BODY>
</HTML>
    '''


class DefaultTemplate(Template):
    ELEMENTS = [IOElement]
    def __call__(self, data, cache, fileBase, width):
        width -= 40
        return '''
        <HTML>

            <BODY bgcolor="#909090">
                {body}
            </BODY>
        </HTML>
            '''.format(body='\n<br>\n'.join([element(data, cache, fileBase, width) for element in self.elements]))


class PlotTemplate(Template):
    ELEMENTS = [IOElement, PlotElement]

    def __call__(self, data, cache, fileBase, width):
        width -= 40
        return '''
        <HTML>

            <BODY bgcolor="#909090">
                {body}
            </BODY>
        </HTML>
            '''.format(body='\n<br>\n'.join([element(data, cache, fileBase, width) for element in self.elements]))


class ProgramTemplate(DefaultTemplate):
    ELEMENTS = [IOElement, StdoutElement]
