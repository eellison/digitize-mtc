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

var SCALE = 8;

var zoom = d3.zoom()
.scaleExtent([1, SCALE])
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



function clicked(d) {
	if (active.node() === this){
		// (sud) For now, do nothing if the active checkbox is clicked
		// Later we may want to fill this in with desired behavior.
		// Ex. We may want the value of the node to change, or reset view like below:
		// active.classed("active", false);
		// return reset();
	}
	// TODO (sud): see if we can avoid the need for parseFloat
		// ie. another way around Javascript defaulting to string concatenation
	active = d3.select(this).classed("active", true);
	var dx = parseFloat(active.attr('width'))
			dy = parseFloat(active.attr('height')),
			center_pt_x = parseFloat(active.attr('x')) + (parseFloat(active.attr('width')) / 2)
		  center_pt_y = parseFloat(active.attr('y')) + (parseFloat(active.attr('height')) / 2)
			scale = Math.max(1, Math.min(8, 0.9 / Math.max(dx / width, dy / height))),
			translate = [width / 2 - scale * center_pt_x, height / 2 - scale * center_pt_y];

	svg.transition()
	.duration(750)
	.call(zoom.transform,
		d3.zoomIdentity
		.translate(translate[0], translate[1])
		.scale(scale)
	);
}

function reset() {
	svg.transition()
	.duration(750)
	.call(zoom.transform,
		d3.zoomIdentity
		.translate(0, 0)
		.scale(1)
	);
}

function panToQuestion(rr, form_width) {
	// TODO (sud): abstract out the logic that is similar to clicked()
	var rr_x = rr.x * width / form_width,
		  rr_y = rr.y * width / form_width,
			dx = rr.w * width / form_width,
			dy = rr.h * width / form_width,
			center_pt_x = parseFloat(rr_x) + (parseFloat(dx) / 2)
		  center_pt_y = parseFloat(rr_y) + (parseFloat(dy) / 2)
			scale = Math.max(1, Math.min(8, 0.9 / Math.max(dx / width, dy / height))),
			translate = [width / 2 - scale * center_pt_x, height / 2 - scale * center_pt_y];
	svg.transition()
	.duration(1111) // (sud) auspicious transition duration length
	.call(zoom.transform,
		d3.zoomIdentity
		.translate(translate[0], translate[1])
		.scale(scale)
	);
}

function edit(q) {
	$(this).parent().removeClass("NotAnswered")
	q.answer_status = "Resolved";

	$(":input", this).each(function (i, d) {

		if (d.type == "text") {
			q.response_regions[i].value = d.value;
		}

		if (d.type == "radio" || d.type == "checkbox"){
			q.response_regions[i].value = d.checked ? "checked" : "empty";;
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
	.attr("class", "question_group");

	// Questions
	var questions = question_groups.selectAll("g.question");
	questions = questions.data(function(d) { return d.questions; }).enter()
	.append("g")
	.merge(questions)
	.attr("class", function(d) { return "question " + d.question_type; });

	// Responses
	var responses = questions.selectAll("rect");
	responses.data(function(d) { return d.response_regions; }).enter()
	.append("rect")
	.merge(responses)
	.attr("class", function(d) { return "response " +  d.value; })
	.attr("x", function(d) { return d.x * width / form.w; })
	.attr("y", function(d) { return d.y * width / form.w; })
	.attr("width", function(d) { return d.w * width / form.w; })
	.attr("height", function(d) { return d.h * width / form.w; })
	.on("click", clicked);

}


function display(form) {

	form_table.selectAll("fieldset").data(form.question_groups).enter()
	.append("fieldset")
	.attr("class", "question_group")
	.each(function(qg) {
		// question group legend
		d3.select(this).append("div")
		.attr("class", "question_group_title")
		.text(qg.name);

		// questions
		d3.select(this).selectAll("div").data(qg.questions).enter()
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
				.attr("name", q.name)
				.attr("value", function(d) { return d.value; })
				.on("focus", function(d) { return panToQuestion(d, form.w); });
			}

			if (q.question_type == "checkbox") {
				responses.selectAll("input").data(q.response_regions).enter()
				.append("input")
				.attr("type", "checkbox")
				.attr("name", q.name)
				.property("checked", function(d) { return d.value; });
			}

			if (q.question_type == "radio") {
				responses.selectAll("input").data(q.response_regions).enter()
				.each(function(d) {

					d3.select(this).append("input")
					.attr("type", "radio")
					.attr("name", q.name)
					.property("checked", function(d) { return d.value; })
					d3.select(this).append("label").text(d.name);
				});
			}
		});

	});

}

function validate(form) {
	var unanswered = [];
	for (var i = 0; i < form.question_groups.length; i++) {
		var a = form.question_groups[i].questions.filter(function(d) { return d.answer_status == "NotAnswered"; })
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
