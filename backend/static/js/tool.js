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
		// Later we may want to fill this in with desired behavior. Example below.
		// active.classed("active", false);
		// return reset();
	}
	// TODO (sud): fix translation to be to center of area, not (x, y)
	active = d3.select(this).classed("active", true);
	svg.transition()
	.duration(750)
	.call(zoom.transform,
		d3.zoomIdentity
		.translate(width / 2, height / 2)
		.scale(SCALE)
		.translate(-(+active.attr('x')), -(+active.attr('y')))
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

function panToQuestion(question_name) {
	// TODO (sud): write this, and make it on focus of text fields / radio buttons / checkboxes
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
				.attr("value", function(d) { return d.value; });
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
	$("form.update").css("display","inline-block");
	$("svg.update").css("display","inline-block");
	$("#upload-file-btn").removeClass("highlighted");
	$("#upload-file-btn").addClass("disabled");
	$("#save-file-btn").removeClass("disabled");
	$("#save-file-btn").addClass("highlighted");

}


$(function() {
	$('#save-file-btn').click(function() {
		$('#save-response').append("<h3>" + validate(form) + "unanswered questions." + "</h3>")
		$.ajax({
			type: 'POST',
			url: '/save',
			data: JSON.stringify(form),
			contentType: false,
			cache: false,
			processData: false,
			success: function(data) {
				if (data.status == 'success') {
					$('#save-response').append("<h3>" + "Save success!" + "</h3>")
				} else if (data.status == 'error') {
					$('#save-response').append("<h3>" + data.error_msg + "</h3>")
				}
			},
			error: function(error) {
				$('#save-response').append("<h3>" + "No response from server" + "</h3>")
			}
		});
	});
});
