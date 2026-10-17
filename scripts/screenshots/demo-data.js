/* Demo data for the README images: a guest car, Danish prices for two days and a plan. */

const HOUR = 3600000;

export function demoState({ now, lang = "da", scene = "planned" }) {
  const midnight = new Date(now);
  midnight.setHours(0, 0, 0, 0);
  // Two days of hourly prices in DKK/kWh incl. tariffs: cheap at night, peaks morning and evening.
  const shape = [
    1.42, 1.31, 1.18, 1.09, 1.06, 1.15, 1.62, 2.31, 2.58, 2.12, 1.84, 1.71,
    1.66, 1.58, 1.61, 1.79, 2.24, 3.12, 3.46, 3.18, 2.41, 1.98, 1.74, 1.55,
    1.38, 1.22, 1.04, 0.92, 0.89, 0.97, 1.41, 2.05, 2.36, 1.94, 1.62, 1.48,
    1.43, 1.37, 1.39, 1.52, 1.96, 2.74, 3.02, 2.86, 2.19, 1.81, 1.6, 1.47,
  ];
  const prices = shape.map((price, i) => ({
    start: new Date(midnight.getTime() + i * HOUR).toISOString(),
    end: new Date(midnight.getTime() + (i + 1) * HOUR).toISOString(),
    price,
  }));
  const at = (h, m = 0) => new Date(midnight.getTime() + h * HOUR + m * 60000).toISOString();

  const plan =
    scene === "ready"
      ? { segments: [], mode: null, speed: null, minutes: null, cost: null, energy: null, savings: null, info: null }
      : {
          segments: scene === "charging" ? [{ start: at(19, 30), end: at(24, 10) }] : [{ start: at(25), end: at(29, 40) }],
          mode: "continuous",
          speed: 12.8,
          minutes: 280,
          cost: 48.31,
          energy: 51.33,
          savings: 63.9,
          charge_now_cost: 112.21,
          average_price: 0.94,
          info: {
            plate: "CX 41 207",
            car: "Kia EV6",
            soc: 20,
            limit: 80,
            inputs: {
              soc: 20, charge_limit: 80, battery_capacity: 77.4, charger_power: 11, charging_efficiency: 90,
              charge_completion_time: "07:00", use_completion_time: true, continuous_charging_preferred: true,
            },
          },
          measured_energy: scene === "charging" ? 18.42 : null,
          measured_cost: scene === "charging" ? 18.04 : null,
        };

  const history = [
    { id: "a", car: "Tesla Model Y", plate: "DE 18 404", start: at(-46), end: at(-41, 10), energy: 44.2, cost: 39.6, savings: 51.2, measured_energy: 43.8, measured_cost: 38.9 },
    { id: "b", car: "Volkswagen ID.4", plate: "BT 77 120", start: at(-118), end: at(-114), energy: 38.7, cost: 41.2, savings: 22.4 },
    { id: "c", car: "Polestar 2", plate: "AK 30 555", start: at(-190), end: at(-185, 30), energy: 57.1, cost: 55.8, savings: 61.0 },
    { id: "d", car: "Renault Zoe", plate: "ZV 92 310", start: at(-262), end: at(-259), energy: 26.4, cost: 30.1, savings: 12.7 },
    { id: "e", car: "Skoda Enyaq", plate: "CP 12 901", start: at(-406), end: at(-401), energy: 49.9, cost: 52.4, savings: 38.3 },
    { id: "f", car: "Kia Niro EV", plate: "AX 64 218", start: at(-500), end: at(-496, 20), energy: 41.0, cost: 44.9, savings: 30.6 },
  ];

  return {
    entry_id: "demo",
    entries: [{ entry_id: "demo", title: "EV Guest" }],
    title: "EV Guest",
    now: new Date(now).toISOString(),
    currency: "DKK",
    status: scene === "ready" ? "ready" : scene === "charging" ? "charging" : "planned",
    error: null,
    charge_now: scene === "charging",
    plan_locked: scene === "charging",
    inputs: {
      license_plate: scene === "ready" ? "" : "CX 41 207",
      soc: 20, charge_limit: 80, battery_capacity: 77.4, charger_power: 11, charging_efficiency: 90,
      charge_completion_time: "07:00", use_completion_time: true, continuous_charging_preferred: true,
    },
    car:
      scene === "ready"
        ? { brand: null, model: null, variant: null, battery: null, model_year: null, match_score: null }
        : { brand: "Kia", model: "EV6", variant: "GT-Line AWD", battery: 77.4, model_year: 2024, match_score: 92 },
    plan,
    prices,
    config: { price_entity: "sensor.energi_data_service", energy_entity: "sensor.lader_energi", lookup: true },
    service_health: { motorapi: true, nhtsa: true, open_ev_data: true },
    history,
    settings: { bill_price: 2.5, payment_text: lang === "da" ? "Betal gerne med MobilePay til 12 34 56 78" : "Please pay to 12 34 56 78" },
  };
}
