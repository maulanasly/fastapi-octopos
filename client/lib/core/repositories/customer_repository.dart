library;

import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../api_client.dart';
import '../models.dart';

final customerRepositoryProvider = Provider<CustomerRepository>(
  (ref) => CustomerRepository(ref.watch(apiClientProvider)),
);

class CustomerRepository {
  final ApiClient api;
  CustomerRepository(this.api);

  Future<List<Customer>> list() async {
    final resp = await api.dio.get<List<dynamic>>('/customers/');
    return resp.data!
        .map((e) => Customer.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<Customer> create({
    required String name,
    String? email,
    String? phone,
  }) async {
    final resp = await api.dio.post<Map<String, dynamic>>(
      '/customers/',
      data: {
        'name': name,
        'email': ?email,
        'phone': ?phone,
      },
    );
    return Customer.fromJson(resp.data!);
  }

  Future<Customer> update(int id, Map<String, dynamic> body) async {
    final resp = await api.dio.put<Map<String, dynamic>>(
      '/customers/$id',
      data: body,
    );
    return Customer.fromJson(resp.data!);
  }

  Future<void> deactivate(int id) async {
    await api.dio.delete('/customers/$id');
  }
}
