/// Tracking hub: active service trips with live positions, opening the
/// trip map for each order.
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/strings.dart';
import 'tracking_controller.dart';

class TrackingScreen extends ConsumerWidget {
  const TrackingScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final s = ref.watch(stringsProvider);
    final state = ref.watch(trackingControllerProvider);

    if (state.trips.isEmpty && state.loading) {
      return const Center(child: CircularProgressIndicator());
    }
    if (state.trips.isEmpty) {
      return Center(child: Text(s.of('trackingEmpty')));
    }
    return RefreshIndicator(
      onRefresh: () => ref.read(trackingControllerProvider.notifier).refresh(),
      child: ListView.separated(
        padding: const EdgeInsets.all(16),
        itemCount: state.trips.length,
        separatorBuilder: (_, _) => const SizedBox(height: 8),
        itemBuilder: (context, index) {
          final trip = state.trips[index];
          return Card(
            child: ListTile(
              leading: Icon(
                _statusIcon(trip.trackingStatus),
                color: Theme.of(context).colorScheme.primary,
              ),
              title: Text(
                '${s.of('orderNumber', args: {'id': trip.orderId})} '
                '· ${_statusLabel(s, trip.trackingStatus)}',
              ),
              subtitle: Text(
                trip.destinationAddress ??
                    (trip.destinationLat != null && trip.destinationLng != null
                        ? '${trip.destinationLat!.toStringAsFixed(5)}, '
                            '${trip.destinationLng!.toStringAsFixed(5)}'
                        : s.of('destination')),
              ),
              trailing: const Icon(Icons.map_outlined),
              onTap: () => context.push(
                '/tracking/${trip.orderId}',
                extra: trip,
              ),
            ),
          );
        },
      ),
    );
  }

  static String _statusLabel(AppStrings s, String status) => switch (status) {
    'assigned' => s.of('statusAssigned'),
    'en_route' => s.of('statusEnRoute'),
    'on_site' => s.of('statusOnSite'),
    _ => status,
  };

  static IconData _statusIcon(String status) => switch (status) {
    'assigned' => Icons.local_shipping_outlined,
    'en_route' => Icons.directions_car_outlined,
    'on_site' => Icons.location_on_outlined,
    _ => Icons.radio_button_unchecked,
  };
}
