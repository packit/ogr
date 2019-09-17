from requre.import_system import upgrade_import_system
from tests.replacements import MODULE_LIST


upgrade_import_system(MODULE_LIST, debug_file="modules.out")
