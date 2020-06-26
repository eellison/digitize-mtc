/////////////////////////////////////////////////////////////////////
// Functionality for pulling image from live stream
/////////////////////////////////////////////////////////////////////
function requestLiveFeedResponse(form_name, page_number) {
  $.ajax({
    type: 'GET',
    url: '/check_alignment/' + form_name + '/' + page_number,
    contentType: false,
    cache: false,
    processData:false,
    success: function(data) {
      if (data.status == 'success') {
        form[page_number] = data;
        d3.select("#turn-on-align-btn").text("Turn on Align Feature");
        d3.select("#videoFeed").classed("camera-feed-green", false);
        d3.select("#videoFeed").classed("camera-feed", true);
        $('#page-box' + page_number).attr("class", "page-box-green");
        $('#file-thumbnail' + page_number).attr('src', "/static/image/checkmark.png");
        current_page = current_page + 1;
      } else if (data.status == 'aligned') {
        console.log("got alignment!!");
        d3.select("#turn-on-align-btn").text(data.remaining_frames);
        d3.select("#videoFeed").classed("camera-feed", false);
        d3.select("#videoFeed").classed("camera-feed-green", true);
        d3.select("#scanning-status-box").classed("text-block", false);
        d3.select("#scanning-status-box").classed("text-block-green", true);
        requestLiveFeedResponse(form_name, page_number);
      } else if (data.status == 'unaligned') {
        console.log("bad alignment...");
        d3.select("#turn-on-align-btn").text("Scanning for page " + (page_number + 1));
        d3.select("#videoFeed").classed("camera-feed-green", false);
        d3.select("#videoFeed").classed("camera-feed", true);

        requestLiveFeedResponse(form_name, page_number);
      }
    },
    error: function(xhr) {
      //Do Something to handle error
      console.log("AJAX error...?");
    }
  });
}

$('#align-switch').click(function(){
    if($(this).is(':checked')){
        requestLiveFeedResponse(file_path, current_page);
        d3.select("#scanning-status-text").text("Scanning for page " + (current_page + 1));
        console.log("ON");
    } else {
        d3.select("#scanning-status-text").text("Scanning feature off...");
        console.log("OFF");
    }
});

$(function() {
	$('#turn-on-align-btn').click(function() {
     d3.select("#turn-on-align-btn").text("Scanning for page " + (current_page + 1));
	   requestLiveFeedResponse(file_path, current_page);
   })
 });

$(function() {
	$('#process-live-feed-btn').click(function() {
        current_page = 0;
        populate_pages_dropdown();
        render_form();
   })
 });

$(function() {
	$('.page-box').click(function() {
     current_page = $('.page-box').index(this);
     // TODO: also highlight this page box and un-highlight the others
     // Basic outline to change the CSS class of the clicked box is below
     // $('.page-box').removeClass(".page-box-active");
     // $('#page-box' + current_page).addClass("page-box-active");
   })
 });

function render_form() {
  clearSVG();
  display(form[current_page]);
  visualize(form[current_page]);
  displaySvgFrame();
  $(".question_group_title").click();
  hideUpload();
}

function upload_files_to_server() {
  var form_data = new FormData($('#upload-file')[0]);
  $.ajax({
    type: 'POST',
    url: '/new_form/',
    data: form_data,
    contentType: false,
    cache: false,
    processData: false,
    success: function(data) {
      if (data.status == 'success') {
        console.log("SUCCESS");
        form = data.pages;
        current_page = 0;
        render_form();
        populate_pages_dropdown();
      } else {
        console.log("NOT A SUCCESS :(");
      }
    },
    error: function(error) {
      console.log(error);
    }
  });
}

var pages_dropdown = document.querySelector('select#pagesDropdown');
pages_dropdown.onchange = function() {
  // NOTE: need to do "value - 1" since the variable form is 0-indexed
  current_page = pages_dropdown.value - 1;
  render_form();
};

function populate_pages_dropdown() {
  for (var i = 1; i <= form.length; i++) {
    var option = document.createElement('option');
    option.value = i;
    option.text = i.toString();
    pages_dropdown.appendChild(option);
  }
}

var width = (document.getElementById("main-content").offsetWidth),
	height = (document.getElementById("main-content").offsetWidth),
	active = d3.select(null);

var ZOOM_BOX_TIGHTNESS = 16; // Higher is tigher

var zoom = d3.zoom()
.scaleExtent([1, ZOOM_BOX_TIGHTNESS])
.on("zoom", zoomed);

var form_table = d3.select("#update").append("form").attr('class', 'update');

var svg = d3.select("#update").append("svg")
.attr('class', 'update')
// .attr("width", width)
// .attr("height", height)
.attr("width", "60%")
.attr("height", "60%")
.attr("viewBox", "0 0 " + width + " " + height)
.attr("preserveAspectRatio", "xMidYMid meet")
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

function clearSVG() {
  // Essentially just remove all the question groups
  // This way when the user switches which page they want to view,
  // rectangles from the previous page no longer visible.
  // TODO (Dan): "Is this abuse of D3, or good form?" - Sud
  form_image.selectAll("g.question_group").remove();
}

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
	updateTempRect(0,0,0,0);
	active = d3.select(null);
}

function getParentNode(childNode) {
	return $(childNode).parent()[0];
}

function updateTempRect(x, y, w, h) {
	form_image.select("#tempRect")
			.attr("x", x)
			.attr("y", y)
			.attr("width", w)
			.attr("height", h);
}

function clicked(d) {
	// Get elements in global form based on SVG element that was clicked
	// TODO (sud): clean this up? seems like sheer hackery
	var parentNode = getParentNode(this);
	var question_type_string = d3.select(parentNode).attr('question_type');
	var response_region_name = d3.select(this).attr("response_region_name");
	var question_name = d3.select(parentNode).attr('question_name');
	var question_group_name = d3.select(getParentNode(parentNode)).attr('question_group_name');
	var question_group = findByName(form[current_page].question_groups, question_group_name);
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
			display(form[current_page]);
			visualize(form[current_page]);

		} else if (question_type_string == "checkbox") {
			var response_region = question.response_regions[0];
			// Flip the response region value on click
			response_region.value = (response_region.value == "checked") ? "empty" : "checked";
			display(form[current_page]);
			visualize(form[current_page]);
		}

	} else {
		const [x, y, w, h]  = getQuestionBoundingCoordinates(question, false);
		const [proj_x, proj_y, proj_w, proj_h]  = getQuestionBoundingCoordinates(question, true);
		active = d3.select(parentNode).classed("active", true);
		d3.select(parentNode).node().focus();
		updateTempRect(x - 1, y - 1, w + 2, h + 2);
		zoomToBoundingBox(1111, proj_x, proj_y, proj_w, proj_h);
	}
}

function panToQuestion(q) {
	const [x, y, w, h]  = getQuestionBoundingCoordinates(q);
	updateTempRect(x - 1, y - 1, w + 2, h + 2);
	zoomToBoundingBox(1111, x, y, w, h);
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

	return project_coordinates(min_x, min_y, boundary_box_width, boundary_box_height, form[current_page].w)

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
	visualize(form[current_page]);
}

function drawRectAroundQuestionRegion( ) {
	return null;
}

function visualize(form) {
	// Images
	var images = form_image.selectAll("image");
	images = images.data([form.image]).enter()
	.append('image')
	.merge(images)
	.attr('xlink:href', function(d) { return ("../static/" + d); })
	.attr('width', "100%")
	.on("click", reset);

	// Add the question bounding box
	form_image.append("rect")
		.attr("id", "tempRect")
		.attr("class", "boundingBox")
		.attr("x", 0)
		.attr("y", 0)
		.attr("width", 0)
		.attr("height", 0);

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
	.attr("class", function(d) {
		if ((d.value == "checked") || (d.value == "empty") || (d.value == "unknown")) {
			return "response " +  d.value;
		} else if (d.value != "") {
			return "response filled";
		} else {
			return "response";
		}
	}).attr("response_region_name", function(d) { return d.name; })
	.attr("x", function(d) { return d.x * width / form.w; })
	.attr("y", function(d) { return d.y * width / form.w; })
	.attr("width", function(d) { return d.w* width / form.w;})
	.attr("height", function(d) { return d.h * width / form.w; })
	.on("click", clicked);

  // $(".question_group_title").click();
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
		var div = d3.select(this).append("div")
			.attr("class",  "question_group_title")
			.text(qg.name);

		// add icons
		div.append("i").attr("class", "fas fa-angle-up");
		div.append("i").attr("class", "fas fa-angle-down").style("display", "none");

		// questions
		d3.select(this).selectAll("div.questions").data(qg.questions).enter()
		.append("div")
		.attr("class", function(d) { return "question " + d.question_type + " " + d.answer_status; })
		.each(function(q) {

			// question label
			d3.select(this).append("label")
				.text(q.name)

			// add location finder
			d3.select(this).append("i")
				.attr("class", "fas fa-search-plus fa-xs")
				.on("click", function(d) { return panToQuestion(q); });

			// responses div
			var responses = d3.select(this).append("div")
			.attr("class", "responses")
			.on("change", edit);

			if (q.question_type == "text" || q.question_type == "digits") {
				responses.selectAll("input").data(q.response_regions).enter()
				.append("input")
				.attr("type", "text")
				.attr("placeholder", "Type Text Here")
				.attr("name", q.name)
				.attr("value", function(d) { return d.value; })
			}

			if (q.question_type == "checkbox") {
				responses.selectAll("input").data(q.response_regions).enter()
				.append("input")
				.attr("type", "checkbox")
				.attr("name", q.name)
				.property("checked", function(d) { return d.value == "checked"; })
			}

			if (q.question_type == "radio") {
				responses.selectAll("input").data(q.response_regions).enter()
				.each(function(d) {

					d3.select(this).append("input")
					.attr("type", "radio")
					.attr("name", q.name)
					.property("checked", function(d) { return d.value == "checked";})
					d3.select(this).append("label").text(d.name);
				});
			}
		});

	});

}


// function validate(form) {
// 	var unanswered = [];
// 	for (var i = 0; i < form.question_groups.length; i++) {
// 		var a = form.question_groups[i].questions.filter(function(d) { return d.answer_status == "unresolved"; })
// 		unanswered = unanswered.concat(a)
// 	}
// 	return unanswered.length
// }

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
		$.ajax({
			type: 'POST',
			url: '/save/' + file_path,
			data: JSON.stringify(form),
			contentType: false,
			cache: false,
			processData: false,
			success: function(data) {
				$('#save-response').empty();

				if (data.status == 'success') {
					$('#save-response').append("<p>" + "Save success!" + "</p>")
					window.location = "/"
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


$(function() {
	$(document).on("click", ".question_group_title", function () {
        var questions = $(this).parent().find(".question");
        questions.toggle();
        var icons = $(this).parent().find("i");
        icons.toggle();
    });
});


$(function() {
	$('#upload-pages-btn').click(function() {
    upload_files_to_server();
	});
});

function check_alignment(input, page_number) {
  var form_data = new FormData($('#upload-file')[0]);
  $.ajax({
    type: 'POST',
    url: '/check_alignment/' + file_path +  "/" + page_number,
    data: form_data,
    contentType: false,
    cache: false,
    processData: false,
    success: function(data) {
      if (data.status == 'success') {
        form[page_number] = data;
        $('#page-box' + page_number).attr("class", "page-box-green");
      } else {
        $('#page-box' + page_number).attr("class", "page-box-red");
      }
    },
    error: function(error) {
      console.log(error);
    }
  });
}

$("input[name='file']").change(function() {
	var index = $("input[name='file']").index(this);
	var file_name = $(this)[0].files[0].name;
	$(this).prev('label').text(file_name);
	readThumbnailAsURL(this, index);
  check_alignment(this, index);
});

function readThumbnailAsURL(input, index) {
  if (input.files && input.files[0]) {
    var reader = new FileReader();

    reader.onload = function(e) {

      $('#file-thumbnail' + index).attr('src', e.target.result);
      $('#file-thumbnail' + index).closest(".page-box-new").removeClass("page-box-new");

    }

    reader.readAsDataURL(input.files[0]);
  }
}
