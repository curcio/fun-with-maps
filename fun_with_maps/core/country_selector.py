#!/usr/bin/env python3
"""
GUI Country Selector Widget

This module provides a GUI interface for selecting a country from a list
of available countries in the world map data.
"""

try:
    import tkinter as tk
    from tkinter import messagebox, ttk
except Exception:  # pragma: no cover - optional dependency
    tk = None
    messagebox = None
    ttk = None
from typing import List, Optional


class CountrySelector:
    """
    A GUI widget for selecting a country from a dropdown list.
    """

    def __init__(self, countries: List[str], title: str = "Select Country"):
        """
        Initialize the country selector.

        Args:
            countries: List of available country names
            title: Window title
        """
        self.countries = countries
        self.selected_country = None
        self.root = None
        self.title = title

    def show_selector(self) -> Optional[str]:
        """
        Show the country selector dialog and return the selected country.

        Returns:
            Selected country name or None if cancelled
        """
        self.root = tk.Tk()
        self.root.title(self.title)
        self.root.geometry("400x300")
        self.root.resizable(True, True)

        # Center the window
        self.root.eval("tk::PlaceWindow . center")

        # Create main frame
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)

        # Title label
        title_label = ttk.Label(
            main_frame, text="🌍 Select a Country to Analyze", font=("Arial", 14, "bold")
        )
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))

        # Search label
        search_label = ttk.Label(main_frame, text="Search/Select Country:")
        search_label.grid(row=1, column=0, sticky=tk.W, pady=(0, 5))

        # Create combobox with search functionality
        self.country_var = tk.StringVar()
        self.combobox = ttk.Combobox(
            main_frame,
            textvariable=self.country_var,
            values=self.countries,
            width=40,
            state="normal",
        )
        self.combobox.grid(
            row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10)
        )

        # Enable search functionality
        self.combobox.bind("<KeyRelease>", self._on_keyrelease)

        # Info label
        info_label = ttk.Label(
            main_frame,
            text=f"Available countries: {len(self.countries)}",
            font=("Arial", 9),
            foreground="gray",
        )
        info_label.grid(row=3, column=0, columnspan=2, pady=(0, 10))

        # Buttons frame
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=4, column=0, columnspan=2, pady=(10, 0))

        # OK button
        ok_button = ttk.Button(
            button_frame,
            text="Analyze Selected Country",
            command=self._on_ok,
            style="Accent.TButton",
        )
        ok_button.pack(side=tk.LEFT, padx=(0, 10))

        # Cancel button
        cancel_button = ttk.Button(button_frame, text="Cancel", command=self._on_cancel)
        cancel_button.pack(side=tk.LEFT)

        # Set default selection if countries available
        if self.countries:
            # Set default to first country or a common one
            default_countries = [
                "United States",
                "Brazil",
                "Argentina",
                "Canada",
                "Australia",
            ]
            for default in default_countries:
                if default in self.countries:
                    self.country_var.set(default)
                    break
            else:
                self.country_var.set(self.countries[0])

        # Bind Enter key to OK
        self.root.bind("<Return>", lambda e: self._on_ok())
        self.root.bind("<Escape>", lambda e: self._on_cancel())

        # Focus on combobox
        self.combobox.focus()

        # Make window modal
        self.root.transient()
        self.root.grab_set()

        # Start the GUI event loop
        self.root.mainloop()

        return self.selected_country

    def _on_keyrelease(self, event):
        """Handle keyrelease event for search functionality."""
        # Get current text
        current_text = self.country_var.get().lower()

        if current_text == "":
            # Show all countries if search is empty
            self.combobox["values"] = self.countries
        else:
            # Filter countries based on current text
            filtered_countries = [
                country for country in self.countries if current_text in country.lower()
            ]
            self.combobox["values"] = filtered_countries

    def _on_ok(self):
        """Handle OK button click."""
        selected = self.country_var.get().strip()

        if not selected:
            messagebox.showwarning("No Selection", "Please select a country.")
            return

        # Validate selection
        if selected not in self.countries:
            # Try to find a close match
            close_matches = [c for c in self.countries if selected.lower() in c.lower()]
            if close_matches:
                # Auto-select the first close match
                selected = close_matches[0]
                self.country_var.set(selected)
            else:
                messagebox.showerror(
                    "Invalid Selection",
                    f"'{selected}' is not a valid country. Please select from the list.",
                )
                return

        self.selected_country = selected
        self.root.destroy()

    def _on_cancel(self):
        """Handle Cancel button click."""
        self.selected_country = None
        self.root.destroy()


def show_country_selector(
    countries: List[str], title: str = "Select Country"
) -> Optional[str]:
    """
    Show a country selector dialog.

    Args:
        countries: List of available country names
        title: Window title

    Returns:
        Selected country name or None if cancelled
    """
    if not countries:
        print("No countries available for selection")
        return None

    try:
        selector = CountrySelector(countries, title)
        return selector.show_selector()
    except Exception as e:
        print(f"Error showing country selector: {e}")
        # Fallback to command line selection
        return _command_line_country_selector(countries)


def _command_line_country_selector(countries: List[str]) -> Optional[str]:
    """
    Fallback command-line country selector.

    Args:
        countries: List of available country names

    Returns:
        Selected country name or None if cancelled
    """
    print("\n🌍 Available Countries:")
    print("=" * 50)

    for i, country in enumerate(countries, 1):
        print(f"{i:3d}. {country}")

    print("\nYou can:")
    print("- Enter a number (1-{})".format(len(countries)))
    print("- Type part of a country name")
    print("- Press Enter to cancel")

    while True:
        try:
            user_input = input("\nSelect country: ").strip()

            if not user_input:
                return None

            # Try to parse as number
            try:
                index = int(user_input) - 1
                if 0 <= index < len(countries):
                    return countries[index]
                else:
                    print(f"Please enter a number between 1 and {len(countries)}")
                    continue
            except ValueError:
                pass

            # Try to match by name
            matches = [c for c in countries if user_input.lower() in c.lower()]

            if len(matches) == 1:
                return matches[0]
            elif len(matches) > 1:
                print(f"\nMultiple matches found ({len(matches)}):")
                for i, match in enumerate(matches[:10], 1):
                    print(f"  {i}. {match}")
                if len(matches) > 10:
                    print(f"  ... and {len(matches) - 10} more")
                print("Please be more specific.")
            else:
                print(f"No countries found matching '{user_input}'")

        except KeyboardInterrupt:
            print("\nSelection cancelled.")
            return None
        except EOFError:
            return None
