from requre.helpers.requests_response import RequestResponseHandling
from requre.import_system import upgrade_import_system

ogr_import_system = (
    upgrade_import_system(debug_file="modules.out")
    .log_imports(what="^requests$", who_name=["ogr", "gitlab", "github"])
    .decorate(
        where="^requests$",
        what="Session.send",
        who_name=[
            "ogr.services.pagure",
            "gitlab",
            "github.MainClass",
            "github.Requester",
        ],
        decorator=RequestResponseHandling.decorator(item_list=[]),
    )
)
