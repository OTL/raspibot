$(function() {
    var data = {};
    ws = new WebSocket("ws://192.168.1.200:8080/chibipibot");
    ws.onopen = function() {
        ws.send('connected');
    };
    ws.onmessage = function(e) {
	//$("#holder").append($('<p>'+e.data+'</p>'));
    };
    $('#go_forward').click(function() {
	ws.send('go_forward')
    });
    $('#go_left').click(function() {
	ws.send('go_left')
    });
    $('#go_right').click(function() {
	ws.send('go_right')
    });
    $('#go_backward').click(function() {
	ws.send('go_backward')
    });
    $('#go_stop').click(function() {
	ws.send('go_stop')
    });
    $('#say_move').click(function() {
	ws.send('say_move')
    });
    $('#say_hello').click(function() {
	ws.send('say_hello')
    });

//    $('#sender').append($('<button/>').text('send').click(function(){
//        ws.send($('#message').val());
//    }));
});
