/// Trip map: destination marker + live service-provider position, with
/// status stepper (en route / on site) and a geolocation report button.
library;

import 'package:flutter/material.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:geolocator/geolocator.dart';
import 'package:latlong2/latlong.dart';

import '../../core/models.dart';
import '../../core/strings.dart';
import 'tracking_controller.dart';

class TripMapScreen extends ConsumerStatefulWidget {
  const TripMapScreen({super.key, required this.trip});

  final TrackedOrder trip;

  @override
  ConsumerState<TripMapScreen> createState() => _TripMapScreenState();
}

class _TripMapScreenState extends ConsumerState<TripMapScreen> {
  final MapController _mapController = MapController();
  bool _locating = false;
  bool _didInitialFit = false;

  @override
  Widget build(BuildContext context) {
    final s = ref.watch(stringsProvider);
    final trips = ref.watch(trackingControllerProvider).trips;
    final live = trips.firstWhere(
      (t) => t.orderId == widget.trip.orderId,
      orElse: () => widget.trip,
    );

    final destination =
        (live.destinationLat != null && live.destinationLng != null)
        ? LatLng(live.destinationLat!, live.destinationLng!)
        : null;
    final provider = (live.latestLocation != null)
        ? LatLng(live.latestLocation!.lat, live.latestLocation!.lng)
        : null;
    final center = provider ?? destination ?? const LatLng(-6.2, 106.8);

    // Fit once, when the first live position arrives (or immediately via
    // onMapReady if both points are already known).
    if (!_didInitialFit && provider != null && destination != null) {
      _didInitialFit = true;
      WidgetsBinding.instance.addPostFrameCallback((_) {
        if (mounted) _fit(provider, destination);
      });
    }

    return Scaffold(
      appBar: AppBar(
        title: Text(s.of('orderNumber', args: {'id': live.orderId})),
      ),
      body: Column(
        children: [
          Expanded(
            child: FlutterMap(
              mapController: _mapController,
              options: MapOptions(
                initialCenter: center,
                initialZoom: 13,
                onMapReady: () {
                  if (provider != null && destination != null) {
                    _fit(provider, destination);
                  }
                },
              ),
              children: [
                TileLayer(
                  urlTemplate: 'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
                  userAgentPackageName: 'com.octopos.client',
                ),
                if (destination != null)
                  MarkerLayer(
                    markers: [
                      Marker(
                        point: destination,
                        width: 40,
                        height: 40,
                        child: Icon(
                          Icons.location_on,
                          color: Colors.red,
                          size: 40,
                        ),
                      ),
                    ],
                  ),
                if (provider != null)
                  MarkerLayer(
                    markers: [
                      Marker(
                        point: provider,
                        width: 40,
                        height: 40,
                        child: Icon(
                          Icons.local_shipping,
                          color: Theme.of(context).colorScheme.primary,
                          size: 40,
                        ),
                      ),
                    ],
                  ),
              ],
            ),
          ),
          _statusStepper(s, live),
          Padding(
            padding: const EdgeInsets.all(12),
            child: Row(
              children: [
                IconButton(
                  tooltip: s.of('recenter'),
                  icon: const Icon(Icons.center_focus_strong),
                  onPressed: (provider != null && destination != null)
                      ? () => _fit(provider, destination)
                      : null,
                ),
                Expanded(
                  child: OutlinedButton.icon(
                    onPressed: _locating ? null : _reportCurrentPosition,
                    icon: _locating
                        ? const SizedBox(
                            width: 16,
                            height: 16,
                            child: CircularProgressIndicator(strokeWidth: 2),
                          )
                        : const Icon(Icons.my_location),
                    label: Text(s.of('useMyLocation')),
                  ),
                ),
                const SizedBox(width: 12),
                if (live.trackingStatus == 'assigned')
                  Expanded(
                    child: FilledButton.icon(
                      onPressed: () => ref
                          .read(trackingControllerProvider.notifier)
                          .transition(live.orderId, 'en_route'),
                      icon: const Icon(Icons.directions_car),
                      label: Text(s.of('startTrip')),
                    ),
                  )
                else if (live.trackingStatus == 'en_route')
                  Expanded(
                    child: FilledButton.icon(
                      onPressed: () => ref
                          .read(trackingControllerProvider.notifier)
                          .transition(live.orderId, 'on_site'),
                      icon: const Icon(Icons.location_on),
                      label: Text(s.of('arrivedOnSite')),
                    ),
                  )
                else
                  Expanded(
                    child: OutlinedButton.icon(
                      onPressed: () => _reportCurrentPosition(),
                      icon: const Icon(Icons.refresh),
                      label: Text(s.of('reportPosition')),
                    ),
                  ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _statusStepper(AppStrings s, TrackedOrder trip) {
    final steps = [
      ('assigned', s.of('statusAssigned')),
      ('en_route', s.of('statusEnRoute')),
      ('on_site', s.of('statusOnSite')),
    ];
    final current = steps.indexWhere((e) => e.$1 == trip.trackingStatus);
    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 8, 16, 0),
      child: Row(
        children: [
          for (var i = 0; i < steps.length; i++) ...[
            Icon(
              i <= current ? Icons.check_circle : Icons.radio_button_unchecked,
              color: i <= current
                  ? Theme.of(context).colorScheme.primary
                  : Colors.grey,
            ),
            const SizedBox(width: 4),
            Expanded(
              child: Text(
                steps[i].$2,
                style: TextStyle(
                  fontWeight: i == current
                      ? FontWeight.bold
                      : FontWeight.normal,
                ),
              ),
            ),
            if (i < steps.length - 1) const SizedBox(width: 4),
          ],
        ],
      ),
    );
  }

  Future<void> _reportCurrentPosition() async {
    setState(() => _locating = true);
    try {
      final position = await Geolocator.getCurrentPosition();
      await ref
          .read(trackingControllerProvider.notifier)
          .reportPosition(
            orderId: widget.trip.orderId,
            lat: position.latitude,
            lng: position.longitude,
          );
    } catch (_) {
      if (mounted) {
        final strings = ref.read(stringsProvider);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(strings.of('locationUnavailable'))),
        );
      }
    } finally {
      if (mounted) setState(() => _locating = false);
    }
  }

  void _fit(LatLng a, LatLng b) {
    final bounds = LatLngBounds.fromPoints([a, b]);
    _mapController.fitCamera(
      CameraFit.bounds(bounds: bounds, padding: const EdgeInsets.all(48)),
    );
  }
}
