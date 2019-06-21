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
					form = data;
					display(form);
					visualize(form);
					displaySvgFrame();
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


var form;

var width = (document.getElementById("main-content").offsetWidth)*0.4,
height = (document.getElementById("main-content").offsetWidth)*0.4
active = d3.select(null);

var ZOOM_BOX_TIGHTNESS = 16; // Higher is tigher

var zoom = d3.zoom()
.scaleExtent([1, ZOOM_BOX_TIGHTNESS])
.on("zoom", zoomed);

var form_table = d3.select("#update").append("form").attr('class', 'update');

var svg = d3.select("#update").append("svg")
.attr('class', 'update')
.attr("width", width)
.attr("height", height)
.call(zoom);

// Add background rect
// Gray background behind the form, clicking it resets the view
svg.append("rect")
  	.attr("class", "background")
    .attr("width", width)
    .attr("height", height)
    .on("click", reset)
		.call(zoom);


var form_image = svg.append("g");


function zoomed() {
	const currentTransform = d3.event.transform;
	form_image.attr("transform", currentTransform);
}

function zoomToBoundingBox(duration, x, y, w, h) {
	var scale = Math.max(1, Math.min(ZOOM_BOX_TIGHTNESS, 0.9 / Math.max(w / width, h / height))),
		  center_pt_x = x + (w / 2)
			center_pt_y = y + (h / 2)
			translate_x = width / 2 - scale * center_pt_x
			translate_y = height / 2 - scale * center_pt_y;

	zoomTo(duration, translate_x, translate_y, scale)
}

function zoomTo(duration, translate_x, translate_y, scale) {
	svg.transition()
	  .duration(duration)
	  .call(zoom.transform,
					d3.zoomIdentity
						.translate(translate_x, translate_y)
						.scale(scale)
	);
}

function reset() {
	zoomTo(750, 0, 0, 1);
	active = d3.select(null);
}

function getParentNode(childNode) {
	return $(childNode).parent()[0];
}

function clicked(d) {
	// Get elements in global form based on SVG element that was clicked
	// TODO (sud): clean this up? seems like sheer hackery
	var parentNode = getParentNode(this);
	var question_type_string = d3.select(parentNode).attr('question_type');
	var response_region_name = d3.select(this).attr("response_region_name");
	var question_name = d3.select(parentNode).attr('question_name');
	var question_group_name = d3.select(getParentNode(parentNode)).attr('question_group_name');
	var question_group = findByName(form.question_groups, question_group_name);
	var question = findByName(question_group.questions, question_name);

	if (active.node() === parentNode) {
		// If the active node is clicked, change the underlying response
		if (question_type_string == "radio") {
			var response_region = findByName(question.response_regions, response_region_name);
			// Set all of the responses to "empty", then check the one that was clicked
			for (var i = 0; i < question.response_regions.length; i++) {
				question.response_regions[i].value = "empty";
			}
			response_region.value = "checked";
			display(form);
			visualize(form);

		} else if (question_type_string == "checkbox") {
			var response_region = question.response_regions[0];
			// Flip the response region value on click
			response_region.value = (response_region.value == "checked") ? "empty" : "checked";
			display(form);
			visualize(form);
		}

	} else {
		const [x, y, w, h]  = getQuestionBoundingCoordinates(question, false);
		const [proj_x, proj_y, proj_w, proj_h]  = getQuestionBoundingCoordinates(question, true);
		active = d3.select(parentNode).classed("active", true);
		d3.select(parentNode).node().focus();
		// TODO (sud): draw rectangle around the newly active question 
		// d3.select("#tempRect").remove();
		// form_image.append("rect")
		// 		.attr("id", "tempRect")
		// 		.attr("x", x)
		// 		.attr("y", y)
		// 		.attr("width", w)
		// 		.attr("height", h);
		zoomToBoundingBox(1111, proj_x, proj_y, proj_w, proj_h);
	}
}

function getQuestionBoundingCoordinates(question) {
	var x_values = question.response_regions.map(function(rr) {
		return rr.x;
 	});
	var y_values = question.response_regions.map(function(rr) {
		return rr.y;
	});
	// dx and dy are the bottom left and top right coordinates of the rects
	var dx_values = question.response_regions.map(function(rr) {
		return rr.x + rr.w;
	});
	var dy_values = question.response_regions.map(function(rr) {
		return rr.y + rr.h;
	});

 	var min_x = Math.min.apply(Math, x_values)
			min_y = Math.min.apply(Math, y_values)
			max_dx = Math.max.apply(Math, dx_values)
			max_dy = Math.max.apply(Math, dy_values)
			boundary_box_width = (max_dx - min_x)
			boundary_box_height = (max_dy - min_y);

	return project_coordinates(min_x, min_y, boundary_box_width, boundary_box_height, form.w)

}

function findByName(json_array, name) {
	for (var i = 0; i < json_array.length; i++) {
  	if (json_array[i].name == name) {
			return json_array[i];
  	}
	}
	return null;
}

function project_coordinates(x, y, w, h, form_width) {
	var x_proj = x * width / form_width,
			y_proj = y * width / form_width,
			w_proj = w * width / form_width,
			h_proj = h * width / form_width;
	return [x_proj, y_proj, w_proj, h_proj]
}

function panToResponseRegion(rr, form_width) {
	const [rr_x, rr_y, rr_w, rr_h] = project_coordinates(rr.x, rr.y, rr.w, rr.h, form_width);
	zoomToBoundingBox(1111, rr_x, rr_y, rr_w, rr_h)
}

function edit(q) {
	$(this).parent().removeClass("unresolved")
	q.answer_status = "Resolved";

	$(":input", this).each(function (i, d) {

		if (d.type == "text") {
			q.response_regions[i].value = d.value;
		}

		if (d.type == "radio" || d.type == "checkbox"){
			q.response_regions[i].value = d.checked ? "checked" : "empty";
		}
	});
	visualize(form);
}


function visualize(form) {
	// Image
	form_image.selectAll("image").data([form.image]).enter()
	.append('image')
	.attr('xlink:href', function(d) { return ("../static/" + d); })
	.attr('width', "100%")
	.on("click", reset);

	// Question Groups
	var question_groups = form_image.selectAll("g.question_group");
	question_groups = question_groups.data(form.question_groups).enter()
	.append("g")
	.merge(question_groups)
	.attr("class", "question_group")
	.attr("question_group_name", function(d) { return d.name; });

	// Questions
	var questions = question_groups.selectAll("g.question");
	questions = questions.data(function(d) { return d.questions; }).enter()
	.append("g")
	.merge(questions)
	.attr("class", function(d) { return "question " + d.question_type; })
	.attr("question_type", function(d) { return d.question_type; })
	.attr("question_name", function(d) { return d.name; });

	// Responses
	var responses = questions.selectAll("rect");
	responses.data(function(d) { return d.response_regions; }).enter()
	.append("rect")
	.merge(responses)
	.attr("class", function(d) { return "response " +  d.value; })
	.attr("response_region_name", function(d) { return d.name; })
	.attr("x", function(d) { return d.x * width / form.w; })
	.attr("y", function(d) { return d.y * width / form.w; })
	.attr("width", function(d) { return d.w * width / form.w; })
	.attr("height", function(d) { return d.h * width / form.w; })
	.on("click", clicked);

}

function display(form) {
	// Clear the existing HTML form, if there is one
	d3.selectAll("form.update").html("");

	// Create a new HTML form based on the "form" json object
	form_table.selectAll("fieldset").data(form.question_groups).enter()
	.append("fieldset")
	.attr("class", "question_group")
	.each(function(qg) {
		// question group legend
		d3.select(this).append("div")
		.attr("class", "question_group_title")
		.text(qg.name);

		// questions
		d3.select(this).selectAll("div.questions").data(qg.questions).enter()
		.append("div")
		.attr("class", function(d) { return "question " + d.question_type + " " + d.answer_status; })
		.each(function(q) {
			// question label
			d3.select(this).append("label").text(q.name);

			// responses div
			var responses = d3.select(this).append("div")
			.attr("class", "responses")
			.on("change", edit);

			if (q.question_type == "text") {
				responses.selectAll("input").data(q.response_regions).enter()
				.append("input")
				.attr("type", "text")
				.attr("placeholder", "Type Text Here")
				.attr("name", q.name)
				.attr("value", function(d) { return d.value; })
				.on("focus", function(d) { return panToResponseRegion(d, form.w); });
			}

			if (q.question_type == "checkbox") {
				responses.selectAll("input").data(q.response_regions).enter()
				.append("input")
				.attr("type", "checkbox")
				.attr("name", q.name)
				.property("checked", function(d) { return d.value == "checked"; })
				// .on("mouseover", function(d) { return panToResponseRegion(d, form.w); })
				.on("focus", function(d) { return panToResponseRegion(d, form.w); });
			}

			if (q.question_type == "radio") {
				responses.selectAll("input").data(q.response_regions).enter()
				.each(function(d) {

					d3.select(this).append("input")
					.attr("type", "radio")
					.attr("name", q.name)
					.property("checked", function(d) { return d.value == "checked";})
					// .on("mouseover", function(d) { return panToResponseRegion(d, form.w); })
					.on("focus", function(d) { return panToResponseRegion(d, form.w); });
					d3.select(this).append("label").text(d.name);
				});
			}
		});

	});

}

function validate(form) {
	var unanswered = [];
	for (var i = 0; i < form.question_groups.length; i++) {
		var a = form.question_groups[i].questions.filter(function(d) { return d.answer_status == "unresolved"; })
		unanswered = unanswered.concat(a)
	}
	return unanswered.length
}

function displaySvgFrame(){
	$("#update").css("display","inline-block");
	$("#save").css("display","block");
	$("#upload").css("display","none");
	$("h1#nav-title").text("Review Annotated Record");

	$("#upload-file-btn").removeClass("highlighted");
	$("#upload-file-btn").addClass("disabled");
	$("#save-file-btn").removeClass("disabled");
	$("#save-file-btn").addClass("highlighted");

}

function hideUpload(){
	$(".upload").css("display","none");
}

$(function() {
	$('#save-file-btn').click(function() {
		$('#save-response').append("<p>" + validate(form) + "unanswered questions." + "</p>")
		$.ajax({
			type: 'POST',
			url: '/save',
			data: JSON.stringify(form),
			contentType: false,
			cache: false,
			processData: false,
			success: function(data) {
				$('#save-response').empty();

				if (data.status == 'success') {
					$('#save-response').append("<p>" + "Save success!" + "</p>")
				} else if (data.status == 'error') {
					$('#save-response').append("<p>" + data.error_msg + "</p>")
				}
			},
			error: function(error) {
				$('#save-response').empty();
				$('#save-response').append("<p>" + "No response from server" + "</p>")
			}
		});
	});
});



$('#file').change(function() {
  var i = $(this).prev('label').clone();
  var file = $('#file')[0].files[0].name;
  $(this).prev('label').text(file);
  $("button#upload-file-btn").removeClass("disabled");
	readThumbnailAsURL(this);
});


$(function() {

	$(document).on("click", ".question_group_title", function () {
        var questions = $(this).parent().find(".question");
        console.log(questions);
        console.log(questions.css("display"));
        if(questions.css("display") === "block"){
        	questions.css("display","none");
        }else{
        	questions.css("display","block");
        }

    });
});


function readThumbnailAsURL(input) {
  if (input.files && input.files[0]) {
    var reader = new FileReader();

    reader.onload = function(e) {
			$('#file-thumbnail').css("display", "block");
			$('#file-thumbnail').css("margin-left", "auto");
			$('#file-thumbnail').css("margin-right", "auto");
			$('#file-thumbnail').css("max-width", "500px");
      $('#file-thumbnail').attr('src', e.target.result);
    }

    reader.readAsDataURL(input.files[0]);
  }
}
