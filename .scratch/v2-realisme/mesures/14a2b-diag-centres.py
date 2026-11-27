"""Ticket 14a2b, diagnostic des réceptions « centre » (10,3 -> 6,4 par match) : variante où `_launch_aerial` prend la
durée de vol de la loi au sol (lobs plus hauts, comme avant le 14a2b), tout le reste inchangé ; variante `pas` : le pas
du moteur garde la loi au sol même en vol (roulement compris), tout le reste inchangé. Usage :
uv run python .scratch/v2-realisme/mesures/14a2b-diag-centres.py [sol|pas] ARGS DE bench_series"""
import sys
sys.path.insert(0, ".")
from v2engine import freinage, hauteur, match
from scripts import bench_series

args = sys.argv[1:]
if args and args[0] == "sol":
    args = args[1:]

    def _launch_aerial(ball, distance_m):
        speed = ball.velocity.length()
        flight = freinage.travel_time_s(distance_m, speed, match.TICK_SECONDS)  # loi au sol
        ball.mode, ball.z, ball.vz = match.SOL, 0.0, hauteur.launch_vz(flight, speed)

    match._launch_aerial = _launch_aerial
if args and args[0] == "pas":
    args = args[1:]
    _step = freinage.step_velocity
    freinage.step_velocity = lambda velocity, dt, airborne=False: _step(velocity, dt)
bench_series.main(args)
