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

    Player.prototype.setBattling = function(yes) {
        if (yes)
            this.flags |= this.State.Battling;
        else
            this.flags &= ~this.State.Battling;
    }

    Player.prototype.isAway = function() {
        return this.flags & this.State.Away;
    }

    Player.prototype.setAway = function(yes) {
        if (yes)
            this.flags |= this.State.Away;
        else
            this.flags &= ~this.State.Away;
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
        this.battles = {};
    }

    Channel.prototype.hasPlayer = function (id) {
        return this.players.indexOf(id) != -1;
    }

    Channel.prototype.addBattle = function(battleId, p1, p2) {
        if (!this.hasPlayer(p1) && !this.hasPlayer(p2)) {
            return false;
        }
        this.battles[battleId] = [p1, p2];

        return true;
    }

    Channel.prototype.removeBattle = function(battleId) {
        if (!battleId in this.battles) {
            return false;
        }
        delete this.battles[battleId];
        return true;
    }

    Channel.prototype.removePlayer = function(id) {
        var i = this.players.indexOf(id);
        if (i != -1) {
            this.players.splice(i,1);

            for (var i in this.battles) {
                if (!this.hasPlayer(this.battles[i][0]) && !this.hasPlayer(this.battles[i][1])) {
                    this.removeBattle(i);
                }
            }
        }
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
    PMs: {},

    getPlayerByName: function(name) {
        for (p in this.players) {
            if (this.players[p].name == name)
                return this.players[p];
        }
    },
    getChannelByName: function(name) {

        for (var i in this.channels) {
            if (this.channels[i].name == name)
                return Data.channels[i];
        }
    }
}

UI = function() {

    var $tabs;
    var $channels;

/*
    var pageLayout;
    var centerLayout;
    var mainLayout;
    var channelsLayout;
*/

    var salt;

    function openChannel() {
        var index = $channels.tabs('option', 'selected');
        var tab =  $("ul li", $channels)[index]
        if (!tab) return;
        var name = tab.firstChild.firstChild.nodeValue;
        return Data.getChannelByName(name);
    }
    function openChannelId() {
        var c = openChannel();
        return c !== undefined ? c.id : undefined;
    }

    function init() {
        // Creating tabs on Players / Battles / Channels
        $tabs = $('#tabs').tabs();

        // Creating channels tabs and it's functionality
        $channels = $('#channels').tabs({
            tabTemplate: "<li><a href='#{href}'>#{label}</a> <span class='ui-icon ui-icon-close'>Close Channel</span></li>",
            panelTemplate: "<div class='chatWrapper'><div class=\"chat ui-widget-content\"></div></div>",
            add: function(event, ui) {
                $("#tabPanels").append(ui.panel);
                var myLayout = $(ui.panel).layout({
                    center__paneSelector: '.chat',
                    initPanes: false,
                    spacing_open: 0,
                    spacing_closed: 0,
                    resizeWithWindow: true,
                });
                mainLayout.resizeAll();
                myLayout.resizeAll();
            },
            select: function(event, ui) {
                // Re-create the playerlist when selecting another channel
                $("#playerlist > li").remove(); 
                var chan = Data.getChannelByName(ui.tab.text);
                for (var i = 0; i < chan.players.length; ++i) {
                    addPlayerToList(Data.players[chan.players[i]]);
                }
            },
            show: $.layout.callbacks.resizeTabLayout
        });
        $channels.tab_counter = 0;
        $("#channels span.ui-icon-close").live("click", function() {
            if ($channels.tabs("length") <= 1) return;
            var index = $("li", $channels).index($( this ).parent());
            $channels.tabs("remove", index);
            var name = $(this).parent()[0].firstChild.firstChild.nodeValue;
            var channel = Data.getChannelByName(name);
            Network.sendLeaveChannel(channel.id);
        });

        // Open PM Dialog when clicking player name
        $("#playerlist li span[class=playerName]").live("click", function() {
             var player = Data.getPlayerByName($(this).text());
             PMDialog(player).dialog("moveToTop");
        });

        /* Open a new channel */
        $("#joinchannel").keydown(function(ev) {
            if (ev.which == 13) { // enter
                ev.preventDefault();
                Network.sendJoinChannel($(this).val());
            }
        });

        // Widgets below channels tabs
        $("#chatmessage").keydown(function(ev) {
             if (ev.which == 13) { // enter
                 ev.preventDefault();
                 Network.sendChannelMessage(openChannelId(), $(this).val());
                 $(this).val("");
             }
        });

        $("#send").button().click(function(e) {
            e.preventDefault();
            var $chatmessage = $("#chatmessage");
            Network.sendChannelMessage(openChannelId(), $chatmessage.val());
            $chatmessage.val("");

        });
        $("#registerbutton").button().click(function(e) {
            e.preventDefault();
            Network.sendRegister();
            $(this).button("disable");
        });
        $("#registerbutton").button("disable");

        // Initializing password dialog prompt
        $("#dialog-password").dialog({
             autoOpen: false,
             height: 200,
             width: 400,
             modal: true,
             close: function(event, ui) {
             }
        });
        $("#dialog-password-ok").click(function() {
            $("#dialog-password").dialog("close");
            Network.sendAskForPass($("#dialog-password-input").val(), salt);
            $("#dialog-password-input").val("");
        });
        $("#dialog-password-cancel").click(function() {
            $("#dialog-password").dialog("close");
            $("#dialog-password-input").val("");
        });

        // Initializing connection dialog prompt
        $("#dialog-connect").dialog({
            autoOpen: true,
            modal: true,
            width: 800,
            position: "top",
        });
        $("#dialog-connect-ok").click(function() {
            $("#dialog-connect").dialog("close");
            
            Network.sendConnect($("#dialog-connect-input-ip").val(), $("#dialog-connect-input-port").val());
            Network.sendLogin($("#dialog-connect-input-name").val());

            if (window.localStorage) {
                localStorage.setItem("hostname", $("#dialog-connect-input-ip").val());
                localStorage.setItem("port", $("#dialog-connect-input-port").val());
                localStorage.setItem("name", $("#dialog-connect-input-name").val());
            }
        });

        if (window.localStorage) {
            $("#dialog-connect-input-ip").val(localStorage.getItem("hostname") || "valssi.fixme.fi");
            $("#dialog-connect-input-port").val(localStorage.getItem("port") || "5080");
            $("#dialog-connect-input-name").val(localStorage.getItem("name") || "Guest");
        }

        // table sorter
        $.tablesorter.addParser({
            id: 'count',
            type: 'numeric',
            is: function() { return false; },
            format: function(s) {
                return s.split("/")[0]
            } 

        });

        // Layouts
        pageLayout = $('body').layout({ 
            name: "pageLayout",
            center__paneSelector: "#centerWrapper",
            north__paneSelector: "#header",
            south__paneSelector: "#footer",
            closable: true, 
            resizable: false, 
            slidable: false, 
            south__initClosed: true, 
            north__initClosed: false,
        });
        centerLayout = $('#centerWrapper').layout({
            name: "centerLayout",
            west__paneSelector: "#tabs",
            center__paneSelector: "#main",
            west__minSize: 200,
            west__size: 380
        });

        mainLayout = $('#main').layout({
            name: "mainLayout",
            resizable: false,
            spacing_open: 0,
            spacing_closed: 0,
            center__paneSelector: "#channels",
            north__paneSelector: "#announcement",
            south__paneSelector: "#buttons",
        });
        channelsLayout = $('#channels').layout({
            name: "channelsLayout",
            resizable: false,
            triggerEventsOnLoad: false,
            spacing_open: 0,
            spacing_closed: 0,
            center__paneSelector: "#tabPanels",
            north__paneSelector: "#tabButtons",
            center__onresize: 
            function() {
                $('.chatWrapper').data("layout").resizeAll();
            }
        });
		tablistLayout = $('#tabs').layout({
            name: "tablistLayout",
            resizable: false,
            triggerEventsOnLoad: false,
            spacing_open: 0,
            spacing_closed: 0,
            north__paneSelector: "#tablistTitles",
            center__paneSelector: "#tablist",
            center__onresize: 
            function() {
                $('#tablist').data("layout").resizeAll();
            }
        });
    }

    var PMDialog = function(player) {
        if (Data.PMs.hasOwnProperty(player.id)) {
            return Data.PMs[player.id];
        } else {
            return createPMDialog(player);
        }
    }
    var createPMDialog = function(player) {
        var pm_dialog = $("<div title='" + player.name + "'><div class='ui-widget-content chatdisplay' style='min-height: 120px; overflow: auto;'></div><input type='text'></div>").dialog({
            height: 220,
            resize: function(ui, event) {
                $(".chatdisplay", this).height($(this).height() - 53);
            },
            close: function(ui, event) {
                delete Data.PMs[player.id];
            },
        });
        $("input", pm_dialog).keydown(function(event) {
            if (event.which == 13) {
                var message = $(this).val();
                if (message.length == 0) {
                    return;
                }
                $(this).val("");
                var me = Data.player;
                $chatdisplay = $(".chatdisplay", pm_dialog);
                $chatdisplay.append(fancyName(userColour(me), me.name) + htmlEscape(message) + "<br>");
                /* Resizes correctly */
                pm_dialog.dialog("resize");
                /* Scrolls to the top */
                var plainElement = $chatdisplay[0];
                plainElement.scrollTop = plainElement.scrollHeight;

                Network.sendSendPM(player.id, message);
            }
        });
        pm_dialog.dialog("open");
        Data.PMs[player.id] = pm_dialog;
        return pm_dialog;
    }

    var Clauses =
    {
        SleepClause: 1,
        FreezeClause: 2,
        DisallowSpectator: 4,
        ItemClause: 8,
        ChallengeCup: 16,
        NoTimeOut: 32,
        SpeciesClause: 64,
        RearrangeTeams: 128,
        SelfKO: 256
    };
    
    var ChallengeDesc = 
    {
        Sent: 0,
        Accepted: 1,
        Cancelled: 2,
        Busy: 3,
        Refused: 4,
        InvalidTeam: 5,
        InvalidGen: 6,
    };

    var Mode =
    {
        Singles: 1,
        Doubles: 2,
        Triples: 3,
        Rotation: 4,
    };
    

    var createChallengeDialog = function(opponent, clauses, mode) {
        var modeText = ["Singles", "Doubles", "Triples", "Rotation"][mode];
        var cc=[];
        var sent = false;
        for (var c in Clauses) {
                cc.push("<li><input type='checkbox' disabled='disabled' " + (Clauses[c] & clauses > 0 ? "checked='checked'" : "") + " value='" + c + "'>" + c + "</li>");
        }
        var clauseHtml = cc.join(""); 
        /*var*/ challenge_dialog = $("<div title='" + opponent.name + " challenged you!'><div class='challengeWindow'>Mode: " + modeText + "Clauses: <ul>" + clauseHtml + "</ul><input name='accept' type='button' value='Accept'><input name='deny' type='button' value='Deny'></div></div>").dialog({
            close: function(ui, event) {
                if (!sent)
                    Network.sendChallengeStuff({id: opponent.id, type: ChallengeDesc.Refused});
            },
        });
        $('input[name=accept]', challenge_dialog).click(function(event) {
            sent = true;
            Network.sendChallengeStuff({id: opponent.id, type: ChallengeDesc.Accepted});
            challenge_dialog.dialog("close");
        });
        $('input[name=deny]', challenge_dialog).click(function(event) {
            sent = true;
            Network.sendChallengeStuff({id: opponent.id, type: ChallengeDesc.Refused});
            challenge_dialog.dialog("close");
        });
        challenge_dialog.dialog("open");
        return challenge_dialog;
    }

    var createBattleDialog = function(battleid, opponent, conf, team) {
        var slot = conf.id[0] == Data.player.id ? 0 : 1;
        var battle_dialog = $("<div title='Battle against " + opponent.name + "'><input type='button' name='forfeit' value='Forfeit'></div>").dialog({
            close: function(ui, event) {
                Network.sendBattleFinished(battleid, 0); // forfeit
                delete Data.battles[battleid];
            }
        });
        $('input[name=forfeit]', battle_dialog).click(function(event) {
            battle_dialog.dialog("close");
        });
        battle_dialog.dialog("open");
        Data.battles[battleid] = {dialog: battle_dialog, opponent: opponent, conf: conf, team: team};
        return battle_dialog;
    }

    var getPlayerFromList = function(id) {
        return $('#player_' + id);
    }

    var getPlayerFromListByName = function(name) {
        return $('#playerlist span[class=playerName]').filter(function(i) { return $(this).text() == name; }).parent();
    }

    var getChannelFromList = function(id) {
        return $('#channel_' + id);
    }

    var updatePlayerInList = function(player) {
        var li = getPlayerFromList(player.id);
        $("span[class=playerName]", li).text(player.name);
        $("span[class~=theme-icon]", li).attr("class", "ui-icon theme-icon theme-icon-" + player.authString() + "-" + player.statusString());
    }

    var addPlayerToList = function(p) {
        var item = "<li style='clear: both;' id='player_" + p.id + "'><span class='playerName' style=\"cursor: pointer; color:"+getColour(p)+"\">" + p.name + "</span><span class=\"ui-icon theme-icon theme-icon-" + p.authString() + "-" + p.statusString() + "\">status</span></li>";
        var target = $('#playerlist li span[class=playerName]').filter(function() {
            return $(this).text() > p.name;
        }).eq(0);
        if (target.length > 0) target.parent().before(item);
        else $('#playerlist').append(item);
    }
    var removePlayerFromList = function(p) {
        var li = getPlayerFromList(p.id);
        li.remove();
    }

    var removePlayer = function(player) {
        for (var i in Data.channels) {
            var channel = Data.channels[i];
            var i = channel.players.indexOf(player);
            if (i != -1)
                channel.players.splice(i,1);
        }
        // remove in any case
        removePlayerFromList(player);
    }

    var removeBattle = function(battleId) {
        for (var i in Data.channels) {
            var channel = Data.channels[i];
            channel.removeBattle(battleId);
        }
        delete Data.battles[battleId];
    }

    var addChannelToList = function(c) {
        var item = $("<li id='channel_" + c.id + "'><span class='channelName' style='cursor: pointer;'>" + c.name + "</span></li>");
        item.click(function(e) {
            Network.sendJoinChannel(c.name);
        });
        var target = $('#channellist').children().filter(function() {
            return $(this).text() > c.name;
        }).eq(0);
        if (target.length > 0) target.before(item);
        else $('#channellist').append(item);
    }

    var removeChannelFromList = function(c) {
        var li = getChannelFromList(c.id);
        li.remove();
    }

    var print = function(channelId, message) {
        var chat = $("#channels " + Data.channels[channelId].chatWidget + " div.chat");
        var h = chat.height();
        chat.append(message + "<br>");
        chat.height(h);
        $(chat).attr({ scrollTop: $(chat).attr("scrollHeight") });
    }

    var printAll = function(message) {
        var chat = $("#channels div.chat");
        var h = chat.height();
        chat.append(message + "<br>");
        chat.height(h);
        $(chat).each(function() {$(this).attr({ scrollTop: $(this).attr("scrollHeight") })});
    }

    var getColour = function(user, name) {
        if (user) {
            colour = userColour(user);
        } else {
            switch (name) {
                case "~~Server~~": colour = "orange"; break;
                case "Welcome Message": colour = "blue"; break;
                default: colour = "#3daa68";
            }
        }
        return colour;
    }
    var userColour = function(user) {
        var color = user.color;
		var colour;
        if (color.color_spec == 1) { // Rgb
            colour = "#" + ('0'+(color.red >> 8).toString(16)).substr(-2) + ('0'+(color.green >> 8).toString(16)).substr(-2) + ('0'+(color.blue >> 8).toString(16)).substr(-2);
        } else if (color.color_spec == 0) { // Invalid
            colour = Theme.getColour(user.id);
        } else { // Too lazy
            colour = Theme.getColour(user.id);
        }
        return colour;
    }

    var fancyName = function(colour, name) {
            return "<span style=\"color: " + colour + ";\"><b>" + name + ":</b></span> ";
    }

    var htmlEscape = function(html) {
        return html.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
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
            var escaped = player && player.auth > 3 ? message : htmlEscape(message);
            return fancyName(colour, user) + escaped;
        } else {
            return htmlEscape(message);
        }
    }

    /* Handler, takes care of anything Network gives */
    function Handler() {}

    Handler.prototype.VersionControl = function(data) {
       $('#server_version').text(data.version);
       $('#server_name').text(data.name);
    }

    Handler.prototype.Announcement = function(data) {
       $('#announcement').html("<center>" + data.announcement + "</center>");
       mainLayout.resizeAll();
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
        // Create channel when ChannelPlayers is send
        $channels.tabs("add", "#channels-" + $channels.tab_counter, Data.channels[data.chanId].name);
        Data.channels[data.chanId].chatWidget = "#channels-" + $channels.tab_counter;
        $channels.tab_counter++;

        var players = data.playerList;
        Data.channels[data.chanId].players = players;
        if (openChannelId() === data.chanId) {
            for (var i = 0; i < data.playerList.length; ++i) {
                addPlayerToList(Data.players[data.playerList[i]]);
            }
        }
    }

    Handler.prototype.PlayersList = function(data) {
        for (var i = 0; i < data.players.length; ++i) {
            var player = new Logic.Player(data.players[i]);
            Data.players[player.id] = player;
        }
    }

    Handler.prototype.EngageBattle = function(data) {
        Data.battles[data.battleId] = [data.playerId1, data.playerId2];
        for (var i in Data.channels) {
            var channel = Data.channels[i];
            channel.addBattle(data.battleId,data.playerId1, data.playerId2);
        }
    }

    Handler.prototype.BattleFinished = function(data) {
        removeBattle(data.battleId);
    }

    Handler.prototype.AddChannel = function(data) {
        var channel = new Logic.Channel(data.chanId, data.chanName);
        Data.channels[channel.id] = channel;
        addChannelToList(channel);
    }

    Handler.prototype.RemoveChannel = function(data) {
        var channel = Data.channels[data.chanId];
        delete Data.channels[data.chanId];
        removeChannelFromList(channel);
    }

    Handler.prototype.JoinChannel = function(data) {
        var player = Data.players[data.playerId];
        var channel = Data.channels[data.chanId];
        channel.players.push(player.id);
        if (openChannelId() === data.chanId) {
            addPlayerToList(player);
        }
        if (data.playerId == Data.player.id) {
            $('#channel_' + channel.id + ' span').addClass('ui-state-active');
        }
        //print(data.chanId, player.name + " joined " + channel.name + ".");
    }

    Handler.prototype.LeaveChannel = function(data) {
        var player = Data.players[data.playerId];
        var channel = Data.channels[data.chanId];

        /* PO sends logout before leavechannel, should be fixed */
        if (typeof(player) == "undefined") {
            return;
        }

        //print(data.chanId, player.name + " left " + channel.name + ".");
        channel.removePlayer(player.id);

        if (openChannelId() === data.chanId) {
            removePlayerFromList(player);
        }
        if (data.playerId == Data.player.id) {
            $('#channel_' + channel.id + ' span').removeClass('ui-state-active');
        }
    }

    Handler.prototype.Logout = function(data) {
        var player = Data.players[data.playerId];
        removePlayer(player);
        printAll(player.name + " quit.");
        delete Data.players[data.playerId];
    }

    Handler.prototype.SendMessage = function(data) {
        var user = data.hasId ? Data.players[data.id].name : "???";
        if (!data.hasChannel) {
            if (data.isHtml)
                printAll(data.message);
            else
                printAll(fancyLine(user, data.message));
        } else {
            if (data.isHtml)
                print(data.channel, data.message);
            else
                print(data.channel, fancyLine(data.user, data.message));
        }
    }

    Handler.prototype.Register = function(data) {
        $("#registerbutton").button("enable");
    }

    Handler.prototype.AskForPass = function(data) {
        $("#dialog-password").dialog("open");
        salt = data.salt;
    }

    Handler.prototype.SendPM = function(data) {
        var playerId = data.playerId;
        var message = data.message;
        var player = Data.players[playerId];
        var pm_dialog = PMDialog(player);
        var $chatdisplay = $(".chatdisplay", pm_dialog);
        $chatdisplay.append(fancyName(userColour(player), player.name) + htmlEscape(message) + "<br>");
        $chatdisplay.height(pm_dialog.height() - 53);
        var plainElement = $chatdisplay[0];
        plainElement.scrollTop = plainElement.scrollHeight;
    }

    Handler.prototype.RegistryAnnouncement = function(data) {
        alert('Reg-announcement: ' + data.announcement);
        $('#announcement').html("<center>" + data.announcement + "</center>");
        mainLayout.resizeAll();
    }

    Handler.prototype.ServerList = function(data) {
        var table = [];
        for (var i = 0; i < data.servers.length; ++i) {
            var maxPlayers = data.servers[i][4] == 0 ? '' : "/" + data.servers[i][4];
            table.push("<tr><td>" + data.servers[i][0] + "</td><td>" + data.servers[i][2] + maxPlayers + "</td><td>" + data.servers[i][3] + ":" + data.servers[i][5] + "</td><td>" + (data.protected ? 'protected' : '') +"</td></tr>"); 
        }
        $("#server-listing tbody").append(table.join(""));
        $("#server-listing tr").click(function() {
            var ip_port = $(":nth-child(3)", this).text().split(":");
            $("#dialog-connect-input-ip").val(ip_port[0]);
            $("#dialog-connect-input-port").val(ip_port[1]);
        });
        $("#server-listing").tablesorter({headers: {1: {sorter: 'count'}}, widgets: ['zebra'], sortList: [[1,1], [0,0]]});
    }

    Handler.prototype.SendTeam = function(data) {
        var player = Data.players[data.player.id] = new Logic.Player(data.player);
        updatePlayerInList(player);
    }

    Handler.prototype.Away = function(data) {
        var player = Data.players[data.playerId];
        player.setAway(data.isAway);
        updatePlayerInList(player);
    }

    Handler.prototype.PlayerKick = function(data) {
        var player = Data.players[data.playerId];
        var src = Data.players[data.srcId];
        printAll("<span style='color: red;'><b>" + player.name + " was kicked by " + src.name + "</b></span>"); 
    }

    Handler.prototype.PlayerBan = function(data) {
        var player = Data.players[data.playerId];
        var src = Data.players[data.srcId];
        printAll("<span style='color: red;'><b>" + player.name + " was banned by " + src.name + "</b></span>"); 
    }

    Handler.prototype.Disconnected = function(data) {
        printAll("<i>Disconnected. Reason: " + data.reason + "</i>");
        Network.disconnect();
    }

    Handler.prototype.ChallengeStuff = function(data) {
        var opponent = Data.players[data.challengeInfo.opp];
        var dialog = createChallengeDialog(opponent, data.challengeInfo.clauses, data.challengeInfo.mode);    
    }

    Handler.prototype.EngageBattle = function(data) {
        if (data.playerId1 == 0) { // my battle!
            var opponent = Data.players[data.playerId2];
            var dialog = createBattleDialog(data.battleId, opponent, data.battleConf, data.teamBattle);  
        }
    }

    return {
        init: init,
        Handler: Handler,
        printAll: printAll,
    }
}();

$(document).ready(function() {
    UI.init();
});
