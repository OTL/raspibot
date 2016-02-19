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
	} catch(e) {
	    alert(e);
	    return;
	}
    };
    $('#go_forward').click(function() {
//	ws.send('{"command_velocity": [100, 0]}')
	ws.send('{"cmd_vel": {"x": 100, "theta": 0}}')
    });
    $('#go_left').click(function() {
//	ws.send('{"cmd_vel": [0, 100]}')
	ws.send('{"cmd_vel": {"x": 0, "theta": 100}}')
    });
    $('#go_right').click(function() {
//	ws.send('{"cmd_vel": [0, -100]}')
	ws.send('{"cmd_vel": {"x": 0, "theta": -100}}')
    });
    $('#go_backward').click(function() {
//	ws.send('{"cmd_vel": [-100, 0]}')
	ws.send('{"cmd_vel": {"x": -100, "theta": 0}}')
    });
    $('#go_stop').click(function() {
//	ws.send('{"cmd_vel": [0, 0]}')
	ws.send('{"cmd_vel": {"x": 0, "theta": 0}}')
    });
    $('#say_move').click(function() {
        ws.send('{"command_speak": "どいてください"}')
    });
    $('#say_hello').click(function() {
        ws.send('{"command_speak": "こんにちは"}')
    });

//    $('#sender').append($('<button/>').text('send').click(function(){
//        ws.send($('#message').val());
//    }));
});
