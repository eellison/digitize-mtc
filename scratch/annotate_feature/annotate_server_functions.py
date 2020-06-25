# Server-side functions to support the annotate feature

@app.route('/create/', methods=['GET', 'POST'])
def create():
	if request.method == "GET":
		return render_template('create.html')
	if request.method == "POST":
		name = request.form['name']
		num_pages = int(request.form['number'])
		# To Do: construct name.json of length number and update global templates
		return render_template('annotate.html', name=name, num_pages=num_pages)

@app.route('/new_form/', methods=['POST', 'GET'])
def new_form():
	if request.method == 'POST':
		files = request.files.getlist("file")
		pages_to_send_back = []
		encoder = FormTemplateEncoder()
		for page_num, file in enumerate(files, start=1):
			# 1) Construct a name/path for the file
			timestamp = "_" + str(time.time())
			page_name = "page_" + str(page_num) + timestamp + ".jpeg"
			upload_location = str(Path.cwd() / "backend" / "static" / page_name)
			# 2) Save the file to that path
			file.save(upload_location)
			# 3) Create an Form object to send back to the frontend
			# TODO (sud): parametrize the form_name
			form_name = "new-form" + "_page_" + str(page_num)
			(x, y) = util.get_image_dimensions(upload_location)
			processed_form = Form(form_name, page_name, y, x, [QuestionGroup()])
			encoded_form = encoder.default(processed_form)
			pages_to_send_back.append(encoded_form)
	return json_status("success", pages=pages_to_send_back)
