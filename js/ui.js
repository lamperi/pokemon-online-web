Logic = function() {

    function Player(playerInfo) {
        this.id = playerInfo.id;
        this.name = playerInfo.name;
        this.info = playerInfo.info;
        this.auth = playerInfo.auth;
        this.color = playerInfo.color;
        this.avatar = playerInfo.avatar;
        this.rating = playerInfo.rating;
        this.flags = playerInfo.flags;
        this.gen = playerInfo.gen;
        this.pokemon = playerInfo.pokemon;
    }

    function Channel(id, name) {
        this.id = id;
        this.name = name;
    }

    function translate() {
        var thing = arguments[0];
        for (var i = 1; i < arguments.length; ++i) {
            thing = thing.replace("%"+i, arguments[i]);
        }
    }

    return {
        Player: Player,
        Channel: Channel,
        tr: translate
    }
}();

Data = {
    players: {},
    channels: {},
    battles: {}
}

UI = function() {

    function init() {
        $('#tabs').tabs();
        $channels = $('#channels').tabs({
            tabTemplate: "<li><a href='#{href}'>#{label}</a> <span class='ui-icon ui-icon-close'>Close Channel</span></li>",
            add: function(event, ui) {
                $(ui.panel).append("<p><div id=\"chat\"></div></p>");
            }
        });
        $channels.tab_counter = 0;
        $("#tabs span.ui-icon-close").live("click", function() {
            var index = $("li", $tabs).index($( this ).parent());
            $tabs.tabs("remove", index);
        });
    }

    var addPlayerToList = function(p) {
        var item = "<li>" + p.name + "</li>";
        var target = $('#playerlist').children().filter(function() {
            return $(this).text() > p.name;
        }).eq(0);
        if (target.length > 0) target.before(item);
        else $('#playerlist').append(item);
    }

    var addChannelToList = function(c) {
        var item = "<li>" + c.name + "</li>";
        var target = $('#channellist').children().filter(function() {
            return $(this).text() > c.name;
        }).eq(0);
        if (target.length > 0) target.before(item);
        else $('#channellist').append(item);
    }

    var print = function(channelId, message) {

    }

    /* Handler, takes care of anything Network gives */
    function Handler() {}

    Handler.prototype.Announcement = function(data) {
       $('#announcement').html(data.announcement);
    }

    Handler.prototype.Login = function(data) {
        var player = new Logic.Player(data.player);
        Data.player = player;
        Data.players[player.id] = player;
        addPlayerToList(player);
    }

    Handler.prototype.TierSelection = function(data) {
        Data.tiers = data.tiers;
    }

    Handler.prototype.ChannelsList = function(data) {
        data.channels.forEach(function(chan) {
            var channel = Data.channels[chan[0]] = new Logic.Channel(chan[0], chan[1]);
            addChannelToList(channel);
        });
    }

    Handler.prototype.JoinChannel = function(data) {
        if (Data.player.id = data.playerId) {
            $channels.tabs("add", "#channels-" + $channels.tab_counter, Data.channels[data.chanId].name);
            $channels.tab_counter++;
        }
    }

    Handler.prototype.ChannelMessage = function(data) {
        print(data.chanId, data.message);
    }

    return {
        init: init,
        Handler: Handler
    }
}();

$(document).ready(function() {
    UI.init();
});
