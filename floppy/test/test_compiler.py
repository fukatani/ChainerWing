from floppy.graph import Graph

if __name__ == '__main__':
    graph = Graph().loadDict('../../examples/mnist.ppy')
    graph.run()
