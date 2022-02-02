import React from 'react';
import ReactDOM from 'react-dom';
import {BrowserRouter as Router, NavLink, Route, Switch} from 'react-router-dom'

import sizes from "../scss/main.scss";
import 'highlight.js/scss/github.scss'
window.sizes = sizes;

import PlotPage from './pages/PlotPage';
import DescriptionPage from './pages/DescriptionPage';
import ModelsPage from './pages/ModelsPage';

const ErrorPage = () => <div className={'error-page'}>Not found</div>;

ReactDOM.render(
    <Router>
        <div className={'container'}>
            <header className={'header'}>
                <h1 className="h1">
                    <NavLink to={`/`}>Aberrations Coverage Repository</NavLink>
                </h1>
                <nav className={'nav'}>
                    <NavLink className={'link'} exact activeClassName={'active'} to={`/`}>
                        <span>Overview</span>
                    </NavLink>
                    <NavLink className={'link'} activeClassName={'active'} to={`/description`}>
                        <span>Description</span>
                    </NavLink>
                    <NavLink className={'link'} activeClassName={'active'} to={`/models`}>
                        <span>Models</span>
                    </NavLink>
                </nav>
            </header>
        </div>
        <section className={'container'}>
            <Switch>
                <Route exact path="/" component={PlotPage} />
                <Route path="/description" component={DescriptionPage} />
                <Route path="/models" component={ModelsPage} />
                <Route path="*" component={ErrorPage} />
            </Switch>
        </section>
        <footer className={'container'}>
            <div className={'bottom'}>2020–2021г.</div>
        </footer>
    </Router>,
    document.getElementById('app')
);

if (module.hot) module.hot.accept();
