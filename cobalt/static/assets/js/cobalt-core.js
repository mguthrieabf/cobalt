window.onerror =
function (message, source, lineno, colno, error) {
    var errorData = {
      'message': message,
      'url': source,
      'num': lineno,
      'colno': colno,
      'Error object': JSON.stringify(error)
    };
    $.post('/support/browser-errors', {
      data: JSON.stringify(errorData)
    });

  return true;
}
