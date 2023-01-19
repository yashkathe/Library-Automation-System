function changeMetaTagForRefresh() {
    if("{{ mode }}" == "DETECTED") {
        document.querySelector("[http-equiv='refresh']").remove();
    }
    if("{{ mode }}" == "NOTDETECTED") {
        var meta = document.createElement('meta');
        meta.httpEquiv = "refresh";
        meta.content = "3";
        document.getElementsByTagName('head')[ 0 ].appendChild(meta);
    }
    else if("{{ mode }}" == "ERRORDETECTED") {
        var meta = document.createElement('meta');
        meta.httpEquiv = "refresh";
        meta.content = "3";
        document.getElementsByTagName('head')[ 0 ].appendChild(meta);
    }
}

changeMetaTagForRefresh()

