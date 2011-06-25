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

    Player.prototype.State = {
        NotLoggedIn: 0,
        LoggedIn: 1,
        Battling: 2,
        Away: 4
    }

    Player.prototype.isBattling = function() {
        return this.flags & this.State.Battling;
    }

    Player.prototype.isAway = function() {
        return this.flags & this.State.Away;
    }

    Player.prototype.authString = function() {
        switch (this.auth) {
            case 3: return "owner";
            case 2: return "admin";
            case 1: return "moderator";
            default: return "user";
        }
    }

    Player.prototype.statusString = function() {
        if (this.isBattling()) return "battle"
        if (this.isAway()) return "away";
        return "avail";
    }

    function Channel(id, name) {
        this.id = id;
        this.name = name;
        this.players = [];
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
    battles: {},

    getPlayerByName: function(name) {
        for (p in this.players) {
            if (this.players[p].name == name)
                return this.players[p];
        }
    },
}

UI = function() {

    var $tabs;
    var $channels;

    function openChannel() {
        var index = $channels.tabs('option', 'selected');
        var tab =  $("ul li", $channels)[index]
        if (!tab) return;
        var name = tab.firstChild.firstChild.nodeValue;
        for (var i in Data.channels) {
            if (Data.channels[i].name == name) {
                return Data.channels[i];
            }
        }
    }

    function init() {
        $tabs = $('#tabs').tabs();
        $channels = $('#channels').tabs({
            tabTemplate: "<li><a href='#{href}'>#{label}</a> <span class='ui-icon ui-icon-close'>Close Channel</span></li>",
            add: function(event, ui) {
                $(ui.panel).append("<p><div class=\"chat ui-widget-content\"></div></p>");
            }
        });
        $channels.tab_counter = 0;
        $("#tabs span.ui-icon-close").live("click", function() {
            var index = $("li", $tabs).index($( this ).parent());
            $channels.tabs("remove", index);
        });

        $("#chatmessage").keydown(function(ev) {
             if (ev.which == 13) { // enter
                 ev.preventDefault();
                 Network.sendChannelMessage(openChannel().id, $(this).val());
                 $(this).val("");
             }
        });
    }

    var addPlayerToList = function(p) {
        var item = "<li><span class='playerName' style=\"color:"+getColour(p)+"\">" + p.name + "</span><span class=\"ui-icon theme-icon theme-icon-" + p.authString() + "-" + p.statusString() + "\">status</span></li>";
        var target = $('#playerlist li span[class=playerName]').filter(function() {
            return $(this).text() > p.name;
        }).eq(0);
        if (target.length > 0) target.before(item);
        else $('#playerlist').append(item);
    }
    var removePlayerFromList = function(p) {
        var li = $('#playerlist span[class=playerName]').filter(function(i) { return $(this).text() == p.name; }).parent();
        li.remove();
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
        var chat = $("#channels #" + Data.channels[channelId].chatWidget + " div.chat");
        chat.append(message + "<br>");
    }
    var printAll = function(message) {
        var chat = $("#channels div.chat");
        chat.append(message + "<br>");
    }

    var getColour = function(user, name) {
        if (user) {
            var color = user.color;
            if (color.spec == 1) { // Rgb
                colours = "#" + user.color.red.toString(16) + user.color.green.toString(16) + user.color.blue.toString(16);
            } else if (color.spec == 0) { // Invalid
                colour = Theme.getColour(user.id);
            } else { // Too lazy
                colour = Theme.getColour(user.id);
            }
        } else {
            switch (name) {
                case "~~Server~~": colour = "orange"; break;
                case "Welcome Message": colour = "blue"; break;
                default: colour = "#3daa68";
            }
        }
        return colour;
    }

    var htmlEscape = function(html) {
        return html.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;");
    }

    var fancyLine = function(user, message) {
        if (message.substring(0,3) == "***") {
            return "<span style='color:magenta'>" + htmlEscape(message) + "</span>";
        }
        if (user) {
            var player = Data.getPlayerByName(user);
            if (player && 0 < player.auth && player.auth <= 3) {
                user = "<i>+" + user + "</i>";
            }
            var colour = getColour(player, user);
            return "<span style=\"color: " + colour + ";\"><b>" + user + ":</b></span> " + htmlEscape(message);
        } else {
            return htmlEscape(message);
        }
    }

    /* Handler, takes care of anything Network gives */
    function Handler() {}

    Handler.prototype.VersionControl = function(data) {
       $('#server_version').text(data.version);
    }

    Handler.prototype.ServerName = function(data) {
       $('#server_name').text(data.name);
    }

    Handler.prototype.Announcement = function(data) {
       $('#announcement').html(data.announcement);
    }

    Handler.prototype.Login = function(data) {
        var player = new Logic.Player(data.player);
        Data.player = player;
        Data.players[player.id] = player;
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

    Handler.prototype.ChannelPlayers = function(data) {

        $channels.tabs("add", "#channels-" + $channels.tab_counter, Data.channels[data.chanId].name);
        Data.channels[data.chanId].chatWidget = "#channels-" + $channels.tab_counter;
        $channels.tab_counter++;

        var players = data.playerList;
        Data.channels[data.chanId].players = players;
        var channel = openChannel();
        if (channel && channel.id === data.chanId) {
            for (var i = 0; i < data.playerList.length; ++i) {
                addPlayerToList(Data.players[data.playerList[i]]);
            }
        }
    }

    Handler.prototype.PlayersList = function(data) {
        var player = new Logic.Player(data.player);
        Data.players[player.id] = player;
    }

    Handler.prototype.JoinChannel = function(data) {
        var player = Data.players[data.playerId];
        var channel = Data.channels[data.chanId];
        channel.players.push(player);
        addPlayerToList(player);
        print(data.chanId, player.name + " joined " + channel.name + ".");
    }

    Handler.prototype.LeaveChannel = function(data) {
        var player = Data.players[data.playerId];
        var channel = Data.channels[data.chanId];
        print(data.chanId, player.name + " left " + channel.name + ".");
        var i = channel.players.indexOf(player);
        if (i != -1)
            channel.players.splice(i,1);
        removePlayerFromList(player);
    }

    Handler.prototype.Logout = function(data) {
        var player = Data.players[data.playerId];
        for (var i in Data.channels) {
            var channel = Data.channels[i];
            var i = channel.players.indexOf(player);
            if (i != -1)
                channel.players.splice(i,1);
        }
        removePlayerFromList(player);
        print(data.chanId, player.name + " quit.");
    }

    Handler.prototype.ChannelMessage = function(data) {
        print(data.chanId, fancyLine(data.user, data.message));
    }

    Handler.prototype.HtmlMessage = function(data) {
        printAll(data.message);
    }

    Handler.prototype.SendMessage = function(data) {
        printAll(fancyLine(data.user, data.message));
    }

    Handler.prototype.Register = function(data) {
        //$("#registerButton").enable();
    }

    return {
        init: init,
        Handler: Handler
    }
}();

$(document).ready(function() {
    UI.init();
});
