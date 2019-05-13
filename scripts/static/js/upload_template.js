$(function() {
    $('button').click(function() {
        $.ajax({
            url: '/template_request',
            data: {} ,
            type: 'POST',
            success: function(response) {
                $( "body").append( "<p>Success</p>" );
                console.log(response);
            },
            error: function(error) {
                $( "body").append( "<p>Failure</p>" );
                console.log(error);
            }
        });
    });
});
