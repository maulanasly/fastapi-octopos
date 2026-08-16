/// App configuration.
///
/// Override at build/run time with:
///   flutter run --dart-define=API_BASE_URL=http://192.168.1.50:8000/api/v1
class AppConfig {
  static const String apiBaseUrl = String.fromEnvironment(
    'API_BASE_URL',
    // 127.0.0.1, not localhost: Chrome resolves localhost to ::1 first and
    // the dev backend (make run) binds IPv4 127.0.0.1 only.
    defaultValue: 'http://127.0.0.1:8000/api/v1',
  );

  /// Project name / display title.
  static const String appTitle = 'OctoPOS';

  /// Origin of the backend (scheme + host + port) for building absolute
  /// media URLs from the relative /media/... paths the API returns.
  static String get mediaBaseUrl {
    final api = apiBaseUrl;
    final cut = api.lastIndexOf('/api/v1');
    return cut > 0 ? api.substring(0, cut) : api;
  }
}
