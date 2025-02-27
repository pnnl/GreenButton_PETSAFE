import { ElectricalUsageRecord } from '../types';

export const electricalUsageMockData: ElectricalUsageRecord[] = [
  // Data from 2020 to present (repeating hourly patterns for simplicity)
  ...Array.from({
    length: (new Date().getFullYear() - 2024 + 1) * 365 * 24*6*4,
  }).map((_, index) => {
    const meterIds = ['1001', '1002', '1003', '1004', '1005', '1006'];
  
    const date = new Date(2024, 0, 1, 0, 0, 0); // Start date: Jan 1, 2020
    const min=Math.floor(index/(meterIds.length))*15
    const hr=Math.floor(min/60)
    const min2=min-hr*60

    date.setHours(date.getHours() + hr); // Increment by index hours
    date.setMinutes(date.getMinutes() + min2)
    const day=date.getDay()

    //console.log(index,date)
    const meterId = meterIds[index % meterIds.length]; // Cycle through meters

    const f1=3.141592*2/(24*60)
    const f2=f1*2


    const kW1 = 4 //Evening load
    const ph1 = -6*60*f1 + (Math.random() *360-180)*f1; // Create a peak ~5:30 pm +/- 2 hr

    const kW2 = 6//Morning+Evening load
    const ph2 = 8*60*f1 + (Math.random() *180-90)*f1; // Create a peak ~6:30 am +/- 1 hr

    const skW1 = (kW1*Math.sin(min*f1+ph1)+5); //Generate the day cycle
    const skW2 = (kW2*Math.sin(min*f2+ph2)+6); //Generate the day cycle
    let value = (skW1+skW2-4).toFixed(2); // Add a slight daily cycle

    if (day>4 && day<7){
      value=value/(Math.random()*.5+2) 
    }
      const usageKw=+value
    return {
      meterId,
      timestamp: date.toISOString(),
      usageKw,
    };
  }),
];
