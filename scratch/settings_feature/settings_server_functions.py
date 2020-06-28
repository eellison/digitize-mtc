## Server-side support of the settings page

@app.route('/settings/')
def settings():
	return render_template('settings.html')
