/// Web print: opens the browser print dialog for the current page.
// ignore_for_file: avoid_web_libraries_in_flutter
library;

import 'dart:js_interop';
import 'dart:js_interop_unsafe';

void printReceipt() {
  globalContext.callMethod('print'.toJS);
}
