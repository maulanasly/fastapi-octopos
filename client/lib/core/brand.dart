/// Branded widgets: Octopus mark + wordmark.
library;

import 'package:flutter/material.dart';
import 'package:flutter_svg/flutter_svg.dart';

/// Octopus mark — teal disc with ink tentacle.
/// Used in login hero (36-40) and AppBar leading (28).
class AppLogo extends StatelessWidget {
  const AppLogo({super.key, this.size = 40, this.showWordmark = false});

  final double size;
  final bool showWordmark;

  @override
  Widget build(BuildContext context) {
    final mark = SvgPicture.asset(
      'assets/brand/octopus-mark.svg',
      width: size,
      height: size,
      semanticsLabel: 'OctoPOS',
    );
    if (!showWordmark) return mark;
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        mark,
        const SizedBox(width: 10),
        SvgPicture.asset(
          'assets/brand/wordmark.svg',
          height: size * 0.52,
          semanticsLabel: 'OctoPOS',
        ),
      ],
    );
  }
}

/// Small inline mark for AppBar (24-28) — no wordmark, tighter.
class AppMark extends StatelessWidget {
  const AppMark({super.key, this.size = 28});

  final double size;

  @override
  Widget build(BuildContext context) {
    return SvgPicture.asset(
      'assets/brand/octopus-mark.svg',
      width: size,
      height: size,
      semanticsLabel: 'OctoPOS mark',
    );
  }
}
