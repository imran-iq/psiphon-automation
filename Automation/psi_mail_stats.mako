## Copyright (c) 2013, Psiphon Inc.
## All rights reserved.
##
## This program is free software: you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation, either version 3 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with this program.  If not, see <http://www.gnu.org/licenses/>.


<style>

  /* Make numbers easier to visually compare. */
  .numcompare {
    text-align: right;
    font-family: monospace;
  }

  /* Some fields are easier to compare left-aligned. */
  .numcompare-left {
    text-align: left;
    font-family: monospace;
  }

  .better {
    background-color: #EFE;
  }

  .worse {
    background-color: #FEE;
  }

  table {
    padding: 0;
    border-collapse: collapse;
    border-spacing: 0;
    font-size: 1em;
    font: inherit;
    border: 0;
  }

  tbody {
    margin: 0;
    padding: 0;
    border: 0;
    font-size: 0.8em;
  }

  table tr {
    border: 0;
    border-top: 1px solid #CCC;
    background-color: white;
    margin: 0;
    padding: 0;
  }

  /* Note that pseudo-selectors don't work with pynliner, so this rule does nothing. */
  table tr:nth-child(2n) {
    background-color: #F8F8F8;
  }

  table tr.row-even {
  }

  table tr.row-odd {
    background-color: #F8F8F8;
  }

  table tr th, table tr td {
    font-size: 1em;
    border: 1px solid #CCC;
    margin: 0;
    padding: 0.5em 1em;
  }

  table tr th {
   font-weight: bold;
    background-color: #F0F0F0;
  }

  table tr td[align="right"] {
    text-align: right;
  }

  table tr td[align="left"] {
    text-align: left;
  }

  table tr td[align="center"] {
    text-align: center;
  }
</style>

<h1>Psiphon 3 Stats</h1>

## Iterate through the tables
% for tablename, tableinfo in data.iteritems():
  <h2>${tablename}</h2>

  <table>

    <thead>
      <tr>
        % for header in tableinfo['headers']:
          <th>${header}</th>
        % endfor
      </tr>
    </thead>

    <tbody>
      % for row_index, row in enumerate(tableinfo['data']):
        <tr class="row${'odd' if row_index%2 else 'even'}">
          ## First column is the region (or Total)
          <th>${row[0]}</th>

          % for col_index, col in enumerate(row[1:]):
            <%
              change = ''
              # Note that this loop starts at row[1], so col_index == 0 is row[1]
              if col_index == 0:
                change = 'better' if row[1] > row[2] else worse
            %>
            <td class="numcompare ${change}">
              ${'{:,}'.format(col)}
            </td>
          % endfor
        </tr>
      % endfor
    </tbody>

  </table>
% endfor