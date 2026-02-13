function handler(event) {
    var request = event.request;
    var uri = request.uri;

    // Check if the URI is missing a file extension
    if (!uri.includes('.')) {
        if (uri.endsWith('/')) {
            request.uri = uri + 'index.html';
        } else {
            request.uri = uri + '/index.html';
        }
    }

    return request;
}
