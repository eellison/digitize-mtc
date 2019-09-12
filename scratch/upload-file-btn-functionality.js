





/////////////////////////////////////////////////////////////////////
// Functionality for sending / receiving the form and editing results
/////////////////////////////////////////////////////////////////////
$(function() {
	$('#upload-file-btn').click(function() {
		var form_data = new FormData($('#upload-file')[0]);

		// json_path is passed in by the template
		$.ajax({
			type: 'POST',
			url: '/upload_and_process_file/' + json_path,
			data: form_data,
			contentType: false,
			cache: false,
			processData: false,
			success: function(data) {
				if (data.status == 'success') {
					$('#upload-response').append("<h3>" + "Upload success!" + "</h3>")
					console.log(data);
					form = data;
					display(form);
					visualize(form);
					displaySvgFrame();
					$(".question_group_title").click();
					hideUpload();
				} else if (data.status == 'error') {
					$('#upload-response').append("<h3>" + data.error_msg + "</h3>")
				}
			},
			error: function(error) {
				$('#upload-response').append("<h3>" + "No response from server" + "</h3>")
			}
		});
	});
});
