import chainer


def main():
    return chainer.datasets.get_mnist(withlabel=False)[0]
