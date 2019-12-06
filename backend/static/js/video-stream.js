///////////////////////////////////////////////////////////////
// Support live video stream on file upload page
//////////////////////////////////////////////////////////////
var videoElement = document.querySelector('video');
var videoSelect = document.querySelector('select#videoSource');

videoSelect.onchange = getStream;

// Grab elements, create settings, etc.
var video = document.getElementById('video');

const hdConstraints = {
	video: {width: {min: 3840}, height: {min: 2160}}
};
// Get access to the camera!
if(navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
	navigator.mediaDevices.enumerateDevices()
	.then(gotDevices).then(getStream).catch(handleError);
}

function gotDevices(deviceInfos) {
	for (var i = 0; i !== deviceInfos.length; ++i) {
		var deviceInfo = deviceInfos[i];
		var option = document.createElement('option');
		option.value = deviceInfo.deviceId;
		if (deviceInfo.kind === 'audioinput') {
			// Do nothing! We only care about streaming video
		} else if (deviceInfo.kind === 'audiooutput'){
			// Do nothing! We only care about streaming video
		} else if (deviceInfo.kind === 'videoinput' && !deviceInfo.label.includes("FaceTime")) {
			// The criteria above is used to filter out a Mac's built-in camera
			// TODO (sud): Figure out a more legitimate way to filter out the build-in camera
			option.text = deviceInfo.label || 'camera ' +
			(videoSelect.length + 1);
			videoSelect.appendChild(option);
		} else {
			console.log('Found one other kind of source/device: ', deviceInfo);
		}
	}
}

function getStream() {
	if (window.stream) {
		window.stream.getTracks().forEach(function(track) {
			track.stop();
		});
	}

	var constraints = {
		video: {
			deviceId: {exact: videoSelect.value},
			width: { ideal: 4096 },
			height: { ideal: 2160 }
		}
	};

	navigator.mediaDevices.getUserMedia(constraints).
	then(gotStream).catch(handleError);
}

function gotStream(stream) {
	window.stream = stream; // make stream available to console
	videoElement.srcObject = stream;
}

function handleError(error) {
	console.log('Error: ', error);
}
