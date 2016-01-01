/*   Copyright (C) 2008-2016 by Nicolas Piganeau and the TS2 TEAM
 *   (See AUTHORS file)
 *
 *   This program is free software; you can redistribute it and/or modify
 *   it under the terms of the GNU General Public License as published by
 *   the Free Software Foundation; either version 2 of the License, or
 *   (at your option) any later version.
 *
 *   This program is distributed in the hope that it will be useful,
 *   but WITHOUT ANY WARRANTY; without even the implied warranty of
 *   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *   GNU General Public License for more details.
 *
 *   You should have received a copy of the GNU General Public License
 *   along with this program; if not, write to the
 *   Free Software Foundation, Inc.,
 *   59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
 */

package ts2

import (
	"encoding/json"
	"fmt"
	"time"
)

type tuplet [3]int

/*
DelayGenerator is a probability distribution for a duration in seconds. It is
used to have random delays of trains.

Its data field is a list of tuplets (arrays of 3 integers).
Each tuple defines in order:
- A lower bound
- An upper bound
- A probability (in percent) of the value to be inside the defined bounds.

e.g. [[0 100 80] [100 500 20]] means that when a value will be yielded by
this DelayGenerator, it will have 80% chance of being between 0 and 100, and
20% chance of being between 100 and 500.
*/
type DelayGenerator struct {
	data []tuplet
}

func (dg *DelayGenerator) UnmarshalJSON(data []byte) error {
	var field []tuplet
	if err := json.Unmarshal(data, &field); err != nil {
		var single int
		if err := json.Unmarshal(data, &single); err != nil {
			return fmt.Errorf("Delay Generator: Unparsable JSON: %s", data)
		}
		dg.data = []tuplet{{single, single, 100}}
	} else {
		dg.data = field
	}
	return nil
}

/*
Time type for the simulation (HH:MM:SS).

Valid Time objects start on 0000-01-02.
*/
type Time struct{ time.Time }

func (h *Time) UnmarshalJSON(data []byte) error {
	var hourStr string
	if err := json.Unmarshal(data, &hourStr); err != nil {
		return fmt.Errorf("Times should be encoded as 00:00:00 strings in JSON, got %s instead", data)
	}
	*h = ParseTime(hourStr)
	return nil
}

/*
ParseTime returns a Time object from its string representation in format 15:04:05
*/
func ParseTime(data string) Time {
	t, err := time.Parse("15:04:05", data)
	if err != nil {
		return Time{}
	}
	// We add 24 hours to make a difference between 00:00:00 and an empty Time
	return Time{t.Add(24 * time.Hour)}
}

/*
Point type represents a point on the scenery
*/
type Point struct {
	X float64
	Y float64
}

func Add(p1 Point, p2 Point) Point {
	return Point{p1.X + p2.X, p1.Y + p2.Y}
}

// A color stored as RGB values
type Color struct {
	R, G, B uint8
}

// Implement the Go color.Color interface.
func (col Color) RGBA() (r, g, b, a uint32) {
	r = uint32(col.R)
	g = uint32(col.G)
	b = uint32(col.B)
	a = 0xFFFF
	return
}

// Hex returns the hex "html" representation of the color, as in #ff0080.
func (col Color) Hex() string {
	return fmt.Sprintf("#%02x%02x%02x", uint8(col.R), uint8(col.G), uint8(col.B))
}

// FromHex parses a "html" hex color-string, either in the 3 "#f0c" or 6 "#ff1034" digits form.
func FromHex(scol string) (Color, error) {
	format := "#%02x%02x%02x"

	var r, g, b uint8
	n, err := fmt.Sscanf(scol, format, &r, &g, &b)
	if err != nil {
		return Color{}, err
	}
	if n != 3 {
		return Color{}, fmt.Errorf("color: %v is not a hex-color", scol)
	}

	return Color{r, g, b}, nil
}

// UnmarshalJSON for the Color type
func (c *Color) UnmarshalJSON(data []byte) error {
	var rawString string
	if err := json.Unmarshal(data, &rawString); err != nil {
		return fmt.Errorf("Unable to read color string: %s (%s)", data, err)
	}
	col, err := FromHex(rawString)
	if err != nil {
		return fmt.Errorf("Unable to decode color: %s (%s)", data, err)
	}
	*c = col
	return nil
}
