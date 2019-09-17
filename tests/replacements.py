from requre.import_system import ReplaceType
from requre.helpers.requests_response import RequestResponseHandling

session_send = {
    "Session.send": [
        ReplaceType.DECORATOR,
        RequestResponseHandling.decorator(item_list=[]),
    ]
}

MODULE_LIST = [
    ("^requests$", {"who_name": "ogr"}),
    ("^requests$", {"who_name": "gitlab"}),
    ("^requests$", {"who_name": "github"}),
    ("^requests$", {"who_name": "ogr.services.pagure"}, session_send),
    ("^requests$", {"who_name": "gitlab"}, session_send),
    ("^requests$", {"who_name": "github.MainClass"}, session_send),
    ("^requests$", {"who_name": "github.Requester"}, session_send),
    ("^requests$", {"who_name": "ogr.services.github_tweak"}, session_send),
]
