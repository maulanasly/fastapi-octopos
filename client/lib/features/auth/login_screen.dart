/// Login / register screen.
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/api_repositories.dart';
import '../../core/auth_controller.dart';
import '../../core/errors.dart';
import '../../core/strings.dart';
import '../../app/theme.dart';

class LoginScreen extends ConsumerStatefulWidget {
  const LoginScreen({super.key});

  @override
  ConsumerState<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends ConsumerState<LoginScreen> {
  final _formKey = GlobalKey<FormState>();
  final _email = TextEditingController();
  final _password = TextEditingController();
  final _fullName = TextEditingController();
  bool _registerMode = false;
  bool _allowRegister = false;
  bool _submitting = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    Future.microtask(() async {
      try {
        final needsSetup = await ref.read(authRepositoryProvider).needsSetup();
        if (mounted) setState(() => _allowRegister = needsSetup);
      } catch (_) {}
    });
  }

  @override
  void dispose() {
    _email.dispose();
    _password.dispose();
    _fullName.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;
    if (_registerMode && !_allowRegister) return;
    setState(() {
      _submitting = true;
      _error = null;
    });
    try {
      if (_registerMode) {
        await ref
            .read(authControllerProvider.notifier)
            .register(
              _email.text.trim(),
              _password.text,
              _fullName.text.trim(),
            );
      } else {
        await ref
            .read(authControllerProvider.notifier)
            .login(_email.text.trim(), _password.text);
      }
      // Router redirects automatically on state change.
    } catch (e) {
      setState(() => _error = friendlyError(e, ref.read(stringsProvider)));
    } finally {
      if (mounted) setState(() => _submitting = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final s = ref.watch(stringsProvider);
    final sessionExpired = ref.watch(authControllerProvider).sessionExpired;
    final scheme = Theme.of(context).colorScheme;
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final wide = MediaQuery.sizeOf(context).width >= 900;

    Widget hero = Container(
      decoration: BoxDecoration(
        gradient: isDark ? AppColors.brandGradientDark : AppColors.brandGradientLight,
      ),
      child: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(32),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Container(
                padding: const EdgeInsets.all(14),
                decoration: BoxDecoration(
                  color: Colors.white.withValues(alpha: 0.14),
                  borderRadius: BorderRadius.circular(16),
                  border: Border.all(color: Colors.white.withValues(alpha: 0.2)),
                ),
                child: const Text('🐙', style: TextStyle(fontSize: 36)),
              ),
              const SizedBox(height: 24),
              Text(
                'OctoPOS',
                style: Theme.of(context).textTheme.displayMedium?.copyWith(
                      color: Colors.white,
                      fontWeight: FontWeight.w900,
                      letterSpacing: -0.03 * 28,
                    ),
              ),
              const SizedBox(height: 12),
              Text(
                'Market teal. Soft ink. Real commerce.',
                style: Theme.of(context).textTheme.titleMedium?.copyWith(
                      color: Colors.white.withValues(alpha: 0.92),
                      fontWeight: FontWeight.w600,
                    ),
              ),
              const SizedBox(height: 8),
              Text(
                'POS, inventory & offline sync — built for the floor, not the template.',
                style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                      color: Colors.white.withValues(alpha: 0.78),
                      height: 1.5,
                    ),
              ),
              const SizedBox(height: 24),
              Wrap(
                spacing: 8,
                runSpacing: 8,
                children: [
                  _HeroPill(icon: Icons.bolt, label: 'F2 Checkout'),
                  _HeroPill(icon: Icons.people_alt_outlined, label: 'F3 Customer'),
                  _HeroPill(icon: Icons.wifi_off, label: 'Offline ready'),
                ],
              ),
            ],
          ),
        ),
      ),
    );

    Widget formCard = Center(
      child: ConstrainedBox(
        constraints: const BoxConstraints(maxWidth: 440),
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(24),
          child: Container(
            padding: const EdgeInsets.all(24),
            decoration: BoxDecoration(
              color: scheme.surfaceContainerLow,
              borderRadius: BorderRadius.circular(24),
              boxShadow: [
                BoxShadow(
                  color: scheme.shadow.withValues(alpha: 0.08),
                  blurRadius: 32,
                  offset: const Offset(0, 12),
                ),
              ],
              border: Border.all(color: scheme.outlineVariant.withValues(alpha: 0.4)),
            ),
            child: Form(
              key: _formKey,
              child: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  if (sessionExpired)
                    Container(
                      margin: const EdgeInsets.only(bottom: 16),
                      padding: const EdgeInsets.all(14),
                      decoration: BoxDecoration(
                        color: scheme.errorContainer,
                        borderRadius: BorderRadius.circular(14),
                        border: Border.all(color: scheme.error.withValues(alpha: 0.2)),
                      ),
                      child: Row(
                        children: [
                          Icon(Icons.info_outline, size: 20, color: scheme.error),
                          const SizedBox(width: 10),
                          Expanded(
                            child: Text(
                              s.of('sessionExpired'),
                              style: Theme.of(context).textTheme.bodySmall?.copyWith(color: scheme.onErrorContainer),
                            ),
                          ),
                        ],
                      ),
                    ),
                  Text(
                    _registerMode ? s.of('createAccount') : s.of('signIn'),
                    style: Theme.of(context).textTheme.titleLarge,
                  ),
                  const SizedBox(height: 6),
                  Text(
                    _registerMode ? 'Create your store — first account becomes admin' : 'Welcome back — sign in to your store',
                    style: Theme.of(context).textTheme.bodySmall?.copyWith(color: scheme.onSurfaceVariant),
                  ),
                  const SizedBox(height: 20),
                  if (_registerMode) ...[
                    TextFormField(
                      key: const Key('fullNameField'),
                      controller: _fullName,
                      decoration: InputDecoration(labelText: s.of('fullName'), prefixIcon: const Icon(Icons.person_outline)),
                      validator: (v) => (v == null || v.trim().isEmpty) ? s.of('required') : null,
                    ),
                    const SizedBox(height: 12),
                  ],
                  TextFormField(
                    key: const Key('emailField'),
                    controller: _email,
                    decoration: InputDecoration(labelText: s.of('email'), prefixIcon: const Icon(Icons.alternate_email)),
                    keyboardType: TextInputType.emailAddress,
                    autocorrect: false,
                    validator: (v) => (v == null || !v.contains('@')) ? 'Valid email required' : null,
                  ),
                  const SizedBox(height: 12),
                  TextFormField(
                    key: const Key('passwordField'),
                    controller: _password,
                    decoration: InputDecoration(labelText: s.of('password'), prefixIcon: const Icon(Icons.lock_outline)),
                    obscureText: true,
                    validator: (v) => (v == null || v.length < 8) ? s.of('minPassword') : null,
                  ),
                  if (_error != null) ...[
                    const SizedBox(height: 12),
                    Container(
                      padding: const EdgeInsets.all(12),
                      decoration: BoxDecoration(
                        color: scheme.errorContainer.withValues(alpha: 0.6),
                        borderRadius: BorderRadius.circular(12),
                      ),
                      child: Text(_error!, style: TextStyle(color: scheme.onErrorContainer, fontSize: 13)),
                    ),
                  ],
                  const SizedBox(height: 20),
                  FilledButton(
                    key: const Key('signInButton'),
                    onPressed: _submitting ? null : _submit,
                    child: _submitting
                        ? const SizedBox(height: 20, width: 20, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                        : Text(_registerMode ? s.of('createAccount') : s.of('signIn')),
                  ),
                  const SizedBox(height: 8),
                  if (_allowRegister)
                    TextButton(
                      onPressed: _submitting ? null : () => setState(() {_registerMode = !_registerMode; _error = null;}),
                      child: Text(_registerMode ? s.of('alreadyHaveAccount') : s.of('newCashierRegister')),
                    )
                  else
                    Padding(
                      padding: const EdgeInsets.only(top: 12),
                      child: Container(
                        padding: const EdgeInsets.all(14),
                        decoration: BoxDecoration(
                          color: scheme.surfaceContainerHighest,
                          borderRadius: BorderRadius.circular(14),
                        ),
                        child: Column(
                          children: [
                            Text(s.of('askManagerToCreateAccount'), textAlign: TextAlign.center, style: Theme.of(context).textTheme.bodySmall?.copyWith(fontWeight: FontWeight.w600)),
                            const SizedBox(height: 4),
                            Text(s.of('contactAdmin'), textAlign: TextAlign.center, style: Theme.of(context).textTheme.bodySmall?.copyWith(color: scheme.onSurfaceVariant)),
                          ],
                        ),
                      ),
                    ),
                ],
              ),
            ),
          ),
        ),
      ),
    );

    return Scaffold(
      backgroundColor: scheme.surface,
      body: wide
          ? Row(
              children: [
                Expanded(flex: 5, child: hero),
                Expanded(flex: 5, child: formCard),
              ],
            )
          : SingleChildScrollView(
              child: Column(
                children: [
                  SizedBox(height: 220, child: hero),
                  formCard,
                ],
              ),
            ),
    );
  }
}

class _HeroPill extends StatelessWidget {
  const _HeroPill({required this.icon, required this.label});
  final IconData icon;
  final String label;
  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      decoration: BoxDecoration(
        color: Colors.white.withValues(alpha: 0.14),
        borderRadius: BorderRadius.circular(999),
        border: Border.all(color: Colors.white.withValues(alpha: 0.2)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 16, color: Colors.white),
          const SizedBox(width: 6),
          Text(label, style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w700, fontSize: 12)),
        ],
      ),
    );
  }
}
