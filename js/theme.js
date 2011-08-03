Theme = function() {
    var url;
    var colours = ["black"]; // default as fallback
    var imagemap = {};

    function init(theme) {
        url = "Themes/" + theme;
        var colours_url = url + "/client/chat_colors.txt";
        $.ajax(colours_url, {
            success: function(data, status, req) {
                colours = data.split("\n");
            },
            error: function(req, text, error) {
                alert("Couldn't load colours: " + error);
            }
        });
        var imagemap_url = url + "/pictures.ini";
        $.ajax(imagemap_url, {
            success: function(data, status, req) {
                var lines = data.split("\n");
                var section;
                for (var i = 0; i < lines.length; ++i) {
                    if (lines[i][0] == "[") {
                        section = lines[i].substring(1, lines[i].length-2);
                    } else if (lines[i].indexOf("=") != -1) {
                        var parts = lines[i].split("=");
                        var values = [];
                        var value = [];
                        var state = 0;
                        for (var j = 0; j < parts[1].length; ++j) {
                            if (state == 0) {
                                if (parts[1][j] == '"') {
                                    state = 1;
                                    value = [];
                                } else {
                                    value.push(parts[1][j]);
                                }
                            } else if (state == 1) {
                                if (parts[1][j] == '"') {
                                    state = 0;
                                    values.push(value.join(""));
                                } else {
                                    value.push(parts[1][j]);
                                }
                            }
                        }
                        imagemap[section + "." + parts[0]] = url + "/" + values;
                    }
                }
                addCss();
            },
            error: function(req, text, error) {
                alert("Couldn't load image map: " + error);
            }
        });
    }

    // Adding CSS dynamically:
    // $(‘<style type=”text/css”>#foo { background: #000; } </style>’).appendTo(“head”);
    function addCss() {
        // Imagemap must be filled already
        var statS = ["avail", "battle", "away"];
        var authS = ["user", "moderator", "admin", "owner"];
        var css = ['<style type="text/css">'];
        css.push(".theme-icon { width: 20px; height: 20px; float: left; } ");
        for (var auth = 0; auth < authS.length; ++auth) {
            for (var s = 0; s < statS.length; ++s) {
                var rule = ".theme-icon-"+authS[auth]+"-"+statS[s]+" { background-image: url(" + imagemap["pictures." + statS[s] + auth] + ") !important;} ";
                css.push(rule);
            }
        }
        css.push(".challengeWindow { background-image: url(" + imagemap["challengebg"] + ") !importan !importantt; }");
        css.push("</style>");
        $(css.join("\n")).appendTo("head");
    }

    function getColour(id) {
        return colours[id % colours.length];
    }

    return {
        init: init,
        getColour: getColour,
        imagemap: imagemap, // debugging
    }
}();

$(document).ready(function() {
    Theme.init("Classic");
});
