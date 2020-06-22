/////////////////////////////////////////////////////////////////////
// Functionality for pulling image from live stream
/////////////////////////////////////////////////////////////////////
function printToTest() {
  // TODO: turn this into a GET request that hits the while loop alignment fn on backend
	console.log("Hit this CODE.");

  $.ajax({
    type: 'GET',
    url: '/video_feed',
    // data: form_data,
    contentType: false,
    success: function(data) {
      if (data.status == 'success') {
        $('#upload-response').append("<h3>" + "Upload success!" + "</h3>")
        form = data;
				console.log(form);
        display(form);
        visualize(form);
        displaySvgFrame();
        $(".question_group_title").click();
        hideUpload();
      } else if (data.status == 'error') {
        $('#upload-response').append("<h3>" + data.error_msg + "</h3>")
      }
    },
    error: function(xhr) {
      //Do Something to handle error
    }
    // cache: false,
    // processData: false,
    // success: function(data) {
    //   if (data.status == 'success') {
    //     $('#upload-response').append("<h3>" + "Upload success!" + "</h3>")
    //     form = data;
    //     display(form);
    //     visualize(form);
    //     displaySvgFrame();
    //     $(".question_group_title").click();
    //     hideUpload();
    //   } else if (data.status == 'error') {
    //     $('#upload-response').append("<h3>" + data.error_msg + "</h3>")
    //   }
    // },
    // error: function(error) {
    //   $('#upload-response').append("<h3>" + "No response from server" + "</h3>")
    // }
  });
}
