# Rebalance to buy-side trading review

Synthetic manual benchmark: NAV1,000, settled cash400,6units at100 and90-percent equity target imply a draft purchase of3units. At10bps quoted fee, cost0.3 and projected cash99.7. The receiver uses ADV100, so participation is3percent and quoted cost0.3. No order is staged or routed.

The common wrapper calls both native validators using the detached source request, maps every receiver leaf, copies quantity without scaling and keeps independent source confirmation open. `tools/test_asset_management_foundations_phase2.py` replays this case plus rehashed forgery, missing mapping and silent-rescaling negatives.
