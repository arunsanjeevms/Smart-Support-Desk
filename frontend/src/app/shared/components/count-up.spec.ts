import { TestBed } from '@angular/core/testing';

import { CountUp } from './count-up';

describe('CountUp', () => {
  function render(inputs: Record<string, unknown>) {
    const fixture = TestBed.createComponent(CountUp);
    for (const [name, value] of Object.entries(inputs)) {
      fixture.componentRef.setInput(name, value);
    }
    fixture.detectChanges();
    return fixture;
  }

  it('shows a dash when there is no value', async () => {
    const fixture = render({ value: null });
    await fixture.whenStable();
    expect(fixture.nativeElement.textContent.trim()).toBe('—');
  });

  it('counts up to the final value with decimals and a suffix', async () => {
    const fixture = render({ value: 33.1, decimals: 1, suffix: ' h', duration: 40 });
    await new Promise((resolve) => setTimeout(resolve, 200));
    fixture.detectChanges();
    expect(fixture.nativeElement.textContent.trim()).toBe('33.1 h');
  });

  it('jumps straight to the value when the duration is zero', async () => {
    const fixture = render({ value: 1250, duration: 0 });
    await fixture.whenStable();
    fixture.detectChanges();
    expect(fixture.nativeElement.textContent.trim()).toBe('1,250');
  });
});
