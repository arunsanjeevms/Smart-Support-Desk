import { TestBed } from '@angular/core/testing';

import { User } from '../core/models/api.models';
import { WelcomeIntro } from './welcome-intro';

const agent = {
  first_name: 'Meera',
  username: 'meera',
  is_agent: true,
} as User;

describe('WelcomeIntro', () => {
  beforeEach(() => vi.useFakeTimers());
  afterEach(() => vi.useRealTimers());

  function render(kind: 'back' | 'new' = 'back') {
    const fixture = TestBed.createComponent(WelcomeIntro);
    fixture.componentRef.setInput('user', agent);
    fixture.componentRef.setInput('kind', kind);
    fixture.detectChanges();
    const finished = vi.fn();
    fixture.componentInstance.finished.subscribe(finished);
    return { fixture, finished };
  }

  it('greets the person by name', () => {
    const { fixture } = render();
    const text = fixture.nativeElement.textContent as string;
    expect(text).toContain('Welcome back, Meera');
    expect(text).toContain('Getting your support queue ready');
  });

  it('says "Welcome" (not "back") after creating an account', () => {
    const { fixture } = render('new');
    expect(fixture.nativeElement.textContent).toContain('Welcome, Meera');
  });

  it('finishes by itself after a couple of seconds', () => {
    const { finished } = render();
    vi.advanceTimersByTime(1000);
    expect(finished).not.toHaveBeenCalled();
    vi.advanceTimersByTime(2000);
    expect(finished).toHaveBeenCalledTimes(1);
  });

  it('can be skipped, and only finishes once', () => {
    const { fixture, finished } = render();
    fixture.nativeElement.querySelector('.skip').click();
    vi.advanceTimersByTime(5000);
    expect(finished).toHaveBeenCalledTimes(1);
  });
});
