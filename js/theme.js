Theme = function() {
    var url;
    var colours = ["black"]; // default as fallback

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
    }

    function getColour(id) {
        return colours[id % colours.length];
    }

    return {
        init: init,
        getColour: getColour,
    }
}();

$(document).ready(function() {
    Theme.init("Classic");
});
