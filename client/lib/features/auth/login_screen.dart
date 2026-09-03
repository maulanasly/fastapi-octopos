/// Login / register screen.
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/api_repositories.dart';
import '../../core/auth_controller.dart';
import '../../core/errors.dart';
import '../../core/strings.dart';

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
    return Scaffold(
      body: Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 420),
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(24),
            child: Form(
              key: _formKey,
              child: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  if (sessionExpired)
                    Container(
                      margin: const EdgeInsets.only(bottom: 12),
                      padding: const EdgeInsets.all(12),
                      decoration: BoxDecoration(
                        color: Theme.of(
                          context,
                        ).colorScheme.surfaceContainerHighest,
                        borderRadius: BorderRadius.circular(10),
                      ),
                      child: Row(
                        children: [
                          Icon(
                            Icons.info_outline,
                            size: 20,
                            color: Theme.of(context).colorScheme.error,
                          ),
                          const SizedBox(width: 8),
                          Expanded(
                            child: Text(
                              s.of('sessionExpired'),
                              style: Theme.of(context).textTheme.bodySmall,
                            ),
                          ),
                        ],
                      ),
                    ),
                  Icon(
                    Icons.storefront,
                    size: 64,
                    color: Theme.of(context).colorScheme.primary,
                  ),
                  const SizedBox(height: 8),
                  Text(
                    'OctoPOS',
                    textAlign: TextAlign.center,
                    style: Theme.of(context).textTheme.headlineMedium,
                  ),
                  const SizedBox(height: 24),
                  if (_registerMode) ...[
                    TextFormField(
                      key: const Key('fullNameField'),
                      controller: _fullName,
                      decoration: InputDecoration(
                        labelText: s.of('fullName'),
                        border: OutlineInputBorder(),
                      ),
                      validator: (v) => (v == null || v.trim().isEmpty)
                          ? s.of('required')
                          : null,
                    ),
                    const SizedBox(height: 12),
                  ],
                  TextFormField(
                    key: const Key('emailField'),
                    controller: _email,
                    decoration: InputDecoration(
                      labelText: s.of('email'),
                      border: OutlineInputBorder(),
                    ),
                    keyboardType: TextInputType.emailAddress,
                    autocorrect: false,
                    validator: (v) => (v == null || !v.contains('@'))
                        ? 'Valid email required'
                        : null,
                  ),
                  const SizedBox(height: 12),
                  TextFormField(
                    key: const Key('passwordField'),
                    controller: _password,
                    decoration: InputDecoration(
                      labelText: s.of('password'),
                      border: OutlineInputBorder(),
                    ),
                    obscureText: true,
                    validator: (v) => (v == null || v.length < 8)
                        ? s.of('minPassword')
                        : null,
                  ),
                  if (_error != null) ...[
                    const SizedBox(height: 12),
                    Text(
                      _error!,
                      style: TextStyle(
                        color: Theme.of(context).colorScheme.error,
                      ),
                    ),
                  ],
                  const SizedBox(height: 20),
                  FilledButton(
                    key: const Key('signInButton'),
                    onPressed: _submitting ? null : _submit,
                    child: _submitting
                        ? const SizedBox(
                            height: 20,
                            width: 20,
                            child: CircularProgressIndicator(strokeWidth: 2),
                          )
                        : Text(
                            _registerMode
                                ? s.of('createAccount')
                                : s.of('signIn'),
                          ),
                  ),
                  if (_allowRegister)
                    TextButton(
                      onPressed: _submitting
                          ? null
                          : () => setState(() {
                              _registerMode = !_registerMode;
                              _error = null;
                            }),
                      child: Text(
                        _registerMode
                            ? s.of('alreadyHaveAccount')
                            : s.of('newCashierRegister'),
                      ),
                    )
                  else
                    Padding(
                      padding: const EdgeInsets.only(top: 8),
                      child: Column(
                        children: [
                          Text(
                            s.of('askManagerToCreateAccount'),
                            textAlign: TextAlign.center,
                            style: Theme.of(context).textTheme.bodySmall,
                          ),
                          const SizedBox(height: 4),
                          Text(
                            s.of('contactAdmin'),
                            textAlign: TextAlign.center,
                            style: Theme.of(context).textTheme.bodySmall?.copyWith(
                                  color: Theme.of(context).colorScheme.onSurfaceVariant,
                                ),
                          ),
                        ],
                      ),
                    ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}
