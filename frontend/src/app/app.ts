import { Component } from '@angular/core';
import { RouterOutlet } from '@angular/router';

/** Root component: everything is rendered by the router. */
@Component({
  selector: 'app-root',
  imports: [RouterOutlet],
  template: '<router-outlet />',
})
export class App {}
