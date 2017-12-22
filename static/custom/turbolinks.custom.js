// Render with http 404 or 500 status #179
// https://github.com/turbolinks/turbolinks/issues/179
// Allow a regular turbolinks render for a 401 response #618
// https://github.com/samvera/hyrax/pull/618
//
// Monkey patch Turbolinks to render 403, 404 & 500 normally
// See https://github.com/turbolinks/turbolinks/issues/179
window.Turbolinks.HttpRequest.prototype.requestLoaded = function() {
  return this.endRequest(function() {
    var code = this.xhr.status;
    if (200 <= code && code < 300 ||
        code === 403 || code === 404 || code === 500) {
      this.delegate.requestCompletedWithResponse(
          this.xhr.responseText,
          this.xhr.getResponseHeader("Turbolinks-Location"));
    } else {
      this.failed = true;
      this.delegate.requestFailedWithStatusCode(code, this.xhr.responseText);
    }
  }.bind(this));
};


// How to display Progress #17
// https://github.com/turbolinks/turbolinks/issues/17
// Provide a method to change the progress bar delay #124
// https://github.com/turbolinks/turbolinks/pull/124
// https://github.com/turbolinks/turbolinks#displaying-progress
// https://github.com/turbolinks/turbolinks/blob/master/src/turbolinks/progress_bar.coffee
//
// Turbolinks.BrowserAdapter.prototype.showProgressBarAfterDelay = function() {
//   return this.progressBarTimeout = setTimeout(this.showProgressBar, 50);
// };
