FileLoader = None
UnitLoader = None
Analyser = None
OnsetSlicer = None
Writer = None
has_aubio = False


try:
    from .aubio_ext import AubioFileLoader
    from .aubio_ext import AubioUnitLoader
    from .aubio_ext import AubioAnalyser
    from .aubio_ext import AubioOnsetSlicer
    from .aubio_ext import AubioWriter
    FileLoader = AubioFileLoader
    UnitLoader = AubioUnitLoader
    Analyser = AubioAnalyser
    OnsetSlicer = AubioOnsetSlicer
    Writer = AubioWriter
    has_aubio = True
except ImportError:
    pass


if has_aubio is False:
    try:
        from .librosa_ext import LibrosaFileLoader
        from .librosa_ext import LibrosaUnitLoader
        FileLoader = LibrosaFileLoader
        UnitLoader = LibrosaUnitLoader
    except ImportError:
        pass
