$("#upload").submit(function(e) {

    e.preventDefault();

    var form = $(this);
    var url = form.attr('action');

    $.ajax({
        url: '/anc_upload_pg_1',
        data: {} ,
        type: 'POST',
        success: function(response) {
            form = response;
  			display(form);
  			visualize(form);
        },
        error: function(error) {
            $( "body").append( "<p>Failure</p>" );
            console.log(error);
        }
    });

});


var form;

var width = (document.getElementById("main-content").offsetWidth)*0.5,
    height = (document.getElementById("main-content").offsetWidth)*0.5;

var zoom = d3.zoom()
    .scaleExtent([1, 10])
    .on("zoom", zoomed);

var svg = d3.select("#update").append("svg")
    .attr('class', 'update')
    .attr("width", width)
    .attr("height", height)
    .append("g")    
    .call(zoom);

var form_image = svg.append("g")
var form_table = d3.select("#update").append("form").attr('class', 'update');



function zoomed() {
    const currentTransform = d3.event.transform;
    form_image.attr("transform", currentTransform);
}

function edit(q) {

	$(this).parent().removeClass("NotAnswered")
	q.answer_status = "Resolved";
	
	$(":input", this).each(function (i, d) {
		
		if (d.type == "text") {
			q.response_regions[i].value = d.value;
		}

		if (d.type == "radio" || d.type == "checkbox"){
			q.response_regions[i].value = d.checked;
		}
	});
	visualize(form);
}


function visualize(form) {

	// Image
	form_image.selectAll("image").data([form.image]).enter()
		.append('image')
    	.attr('xlink:href', function(d) { return d; })
    	.attr('width', "100%")

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
		.attr("height", function(d) { return d.h * width / form.w; });

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
	                        		.property("checked", function(d) { return d.value; });
	                        	d3.select(this).append("label").text(d.name);
	        				});
	        		}

	        		// if (q.question_type == "select") {
	        		// 	responses.selectAll("input").data(q.response_regions).enter()
	        		// 		.each(function(d) {
	  
	        		// 			d3.select(this).append("select")
	          //               		.attr("name", "see")
	          //               		.attr("name", q.name)
	          //               		.property("checked", function(d) { return d.value; });
	          //               	d3.select(this).append("label").text(d.name);
	        		// 		});
	        		// }

				});

		});

}


// document.getElementById('file-download')
// .addEventListener('click', function() {
// 	var unanswered = [];
// 	for (var i = 0; i < form.question_groups.length; i++) {
// 		var a = form.question_groups[i].questions.filter(function(d) { return d.answer_status == "NotAnswered"; })
// 		unanswered = unanswered.concat(a)
// 	}
// 	if (unanswered.length) {
// 		alert(unanswered.length + " questions not filled (in bold)!")
// 	} else {
// 		alert("Success!")
// 	}
// 	console.log(form);
// });