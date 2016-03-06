$(function() {
    var data = {};
    var picker1 = document.getElementById('color_picker1')
    Beehive.Picker(picker1, 1)
    var picker2 = document.getElementById('color_picker2')
    Beehive.Picker(picker2, 2)
    convert_to_rgb = function(str) {
	return '{"r": ' + parseInt(str.substring(1, 3), 16) * 100 / 255 + ', ' +
	    '"g": ' + parseInt(str.substring(3, 5), 16) * 100 / 255 + ', ' +
	    '"b": ' + parseInt(str.substring(5, 7), 16) * 100 / 255 + '}'
    };
    picker1.addEventListener('click', function(e){
	var color = Beehive.getColorCode(e.target);
	if (!color) { 
	    console.log('it is not beehive picker color elemnt.');
	} else {
	    var json_str_color = '{"led1": ' + convert_to_rgb(color) + '}';
	    console.log(json_str_color);
	    ws.send(json_str_color);
	}
	console.log(color);
    });
    picker2.addEventListener('click', function(e){
	var color = Beehive.getColorCode(e.target);
	if (!color) { 
	    console.log('it is not beehive picker color elemnt.');
	} else {
	    var json_str_color = '{"led2": ' + convert_to_rgb(color) + '}';
	    console.log(json_str_color);
	    ws.send(json_str_color);
	}
	console.log(color);
    });

    ws = new WebSocket("ws://smilerobotics.com:9090/chibipibot");
    ws.onopen = function() {
        //ws.send('connected');
	console.log('open');
    };
    ws.onerror = function(error) {
	console.log('ws error' + error);
    }
    ws.onclose = function() {
	
    }
    ws.onmessage = function(e) {
	try {
	    var msg = $.parseJSON(e.data);
	    if (msg.events) {
		// {"events": [
		//   {"time": "2015/02/2 10:30:22",
		//    "text": "Found faces!",
		//    "id": 29023092332},
		//   {"time": "2015/02/2 10:30:23",
		//    "text": "Found faces!",
		//    "id": 29023092333} ] }
		for (var i = 0; i < msg.events.length; i++) {
		    $("#events").append($('<tr><td>' + msg.events[i].time + '</td>' +
					  '<td>' + msg.events[i].text + '</td>' +
					  '</tr>'));
		}
	    }
	    if (msg.sensor) {
		$("#sensors").empty();
		var text = ''
		for (key in msg.sensor) {
		    text += '<tr><td>' + key + '</td>' +
			'<td>' + msg.sensor[key] + '</td>' +
			'</tr>'
		}
		$("#sensors").append(text);
	    }
	    if (msg.battery) {
		$('#battery_percent').text(msg.battery['percent']);
		var battery_level = msg.battery['percent'] / 20;
		for (var i = 0; i < 5; i++) {
		    if (i < battery_level) {
			if (msg.battery['is_charging']) {
			    $('#battery_icon' + i).addClass('glyphicon-flash');
			} else {
			    $('#battery_icon' + i).addClass('glyphicon-apple');
			}
		    } else {
			$('#battery_icon' + i).removeClass('glyphicon-flash glyphicon-apple');
		    }
		}
	    }
	} catch(e) {
	    alert(e);
	    return;
	}
    };

    var stop_command = function() {
	ws.send('{"cmd_vel": {"x": 0, "theta": 0}}')
    };

    $('#go_forward').click(function() {
	ws.send('{"cmd_vel": {"x": 100, "theta": 0}}');
	setTimeout(stop_command, 200);
    });
    $('#go_left').click(function() {
//	ws.send('{"cmd_vel": [0, 100]}')
	ws.send('{"cmd_vel": {"x": 0, "theta": 100}}')
	setTimeout(stop_command, 200);
    });
    $('#go_right').click(function() {
//	ws.send('{"cmd_vel": [0, -100]}')
	ws.send('{"cmd_vel": {"x": 0, "theta": -100}}')
	setTimeout(stop_command, 200);
    });
    $('#go_backward').click(function() {
//	ws.send('{"cmd_vel": [-100, 0]}')
	ws.send('{"cmd_vel": {"x": -100, "theta": 0}}')
	setTimeout(stop_command, 200);
    });
    $('#go_stop').click(function() {
//	ws.send('{"cmd_vel": [0, 0]}')
	ws.send('{"cmd_vel": {"x": 0, "theta": 0}}')
    });
    var speak = function(msg) {
        ws.send('{"sound": {"speak": "' + msg + '"}}')
    };
    $('#say_move').click(function() {
	speak('どいてください')
    });
    $('#say_hello').click(function() {
	speak('こんにちわ');
    });
    $('#play_chime').click(function() {
        ws.send('{"sound": {"sound": "chime"}}')
    });

    $('#speak_send').click(function(){
	speak($('#speak_text').val());
    });
});
