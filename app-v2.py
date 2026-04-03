import matplotlib
import matplotlib.pyplot as plt
import flet as ft
import os
import numpy as np
from scipy import stats

from flet.matplotlib_chart import MatplotlibChart

path = ''
chart_array = []
path_array = set()
title = ''
x_label = ''
y_label = ''
grid = False
grid_minor = False
legend = False
count_function = 0
current_theme = 'dark'

# New global variables for axis settings
fig_width = 8
fig_height = 5
fig_dpi = 100
x_min = None
x_max = None
y_min = None
y_max = None
x_ticks = None
y_ticks = None


class slot_delete(ft.Column):
    def __init__(self):
        super().__init__()
        self.controls = []
        self.spacing = 10
        self.scroll = ft.ScrollMode.AUTO

    def push_element(self, new_element):
        self.controls.append(new_element)

    def clear(self):
        self.controls.clear()


class btn_delete(ft.FilledTonalButton):
    def __init__(self, text, icon_color, icon, on_delete_callback=None):
        super().__init__()
        self.text = text
        self.icon_color = icon_color
        self.icon = icon
        self.on_delete_callback = on_delete_callback
        self.on_click = self.click

    def click(self, e):
        if self.on_delete_callback:
            self.on_delete_callback(self.text)


def main(page: ft.Page):
    page.title = 'Graphic Assistant'
    global current_theme
    page.theme_mode = current_theme
    page.window.width = 1524
    page.window.min_width = 1524
    page.window.height = 720
    page.window.min_height = 720
    page.padding = 10

    matplotlib.use("svg")

    # Create an instance of slot_delete
    delete_slot = slot_delete()

    ####################################################################################################################
    # functions
    ####################################################################################################################

    def apply_theme_to_plot(fig, ax, theme):
        """Apply color theme to matplotlib figure and axes"""
        if theme == 'dark':
            # Dark theme
            fig.patch.set_facecolor('#1e1e1e')
            ax.set_facecolor('#2d2d2d')
            ax.spines['bottom'].set_color('white')
            ax.spines['left'].set_color('white')
            ax.spines['top'].set_color('white')
            ax.spines['right'].set_color('white')
            ax.xaxis.label.set_color('white')
            ax.yaxis.label.set_color('white')
            ax.title.set_color('white')
            ax.tick_params(colors='white')
            # Legend
            if ax.get_legend():
                ax.legend(facecolor='#2d2d2d', edgecolor='white', labelcolor='white')
            # Grid
            ax.grid(True, alpha=0.3, color='gray')
            if grid_minor:
                ax.grid(which='minor', linewidth=0.5, linestyle='--', alpha=0.3, color='gray')
        else:
            # Light theme
            fig.patch.set_facecolor('white')
            ax.set_facecolor('white')
            ax.spines['bottom'].set_color('black')
            ax.spines['left'].set_color('black')
            ax.spines['top'].set_color('black')
            ax.spines['right'].set_color('black')
            ax.xaxis.label.set_color('black')
            ax.yaxis.label.set_color('black')
            ax.title.set_color('black')
            ax.tick_params(colors='black')
            if ax.get_legend():
                ax.legend(facecolor='white', edgecolor='black', labelcolor='black')
            # if grid:
            #     ax.grid(True, alpha=0.3, color='gray')
            # if grid_minor:
            #     ax.grid(which='minor', linewidth=0.5, linestyle='--', alpha=0.3, color='gray')

    def perform_polyfit(x_array, y_array, degree):
        """Perform polynomial approximation"""
        try:
            # Remove possible NaN and inf
            valid_indices = ~(np.isnan(x_array) | np.isnan(y_array) |
                              np.isinf(x_array) | np.isinf(y_array))
            x_clean = np.array(x_array)[valid_indices]
            y_clean = np.array(y_array)[valid_indices]

            if len(x_clean) < degree + 1:
                return None, None, f"Not enough points for approximation of degree {degree}"

            # Perform approximation
            coefficients = np.polyfit(x_clean, y_clean, degree)
            polynomial = np.poly1d(coefficients)

            # Create a smooth line for display
            x_smooth = np.linspace(min(x_clean), max(x_clean), 200)
            y_smooth = polynomial(x_smooth)

            # Calculate R² for quality assessment
            y_pred = polynomial(x_clean)
            ss_res = np.sum((y_clean - y_pred) ** 2)
            ss_tot = np.sum((y_clean - np.mean(y_clean)) ** 2)
            r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0

            return x_smooth, y_smooth, f"R² = {r_squared:.4f}"

        except Exception as e:
            return None, None, f"Approximation error: {str(e)}"

    def draw_chart(e):
        plt.style.use('dark_background')
        try:
            fig, ax = plt.subplots(figsize=(fig_width, fig_height), dpi=fig_dpi)

            global chart_array, title, x_label, y_label, grid, grid_minor, legend
            global x_min, x_max, y_min, y_max, x_ticks, y_ticks

            # Build charts
            for chart in chart_array:
                try:
                    x_array, y_array = [], []
                    with open(chart['path'], 'r') as file:
                        for line in file:
                            line = line.strip()
                            if line and not line.startswith('#'):
                                data = line.split()
                                if len(data) >= 2:
                                    x_array.append(float(data[0]))
                                    y_array.append(float(data[1]))

                    if x_array and y_array:
                        # Display points
                        ax.scatter(x_array, y_array,
                                   color=chart['color'],
                                   marker=chart['marker'] if chart['marker'] != ' ' else 'o',
                                   s=30, alpha=0.6, label=f"{chart['label']} (points)")

                        # Select connection type
                        fit_type = chart.get('fit_type', 'line')

                        if fit_type == 'line':
                            # Simple line connection
                            ax.plot(x_array, y_array,
                                    color=chart['color'],
                                    linestyle=chart['linestyle'],
                                    linewidth=float(chart['linewidth']),
                                    alpha=0.8, label=f"{chart['label']} (line)")

                        elif fit_type == 'polyfit':
                            # Polynomial approximation
                            degree = chart.get('polyfit_degree', 1)
                            x_smooth, y_smooth, info = perform_polyfit(x_array, y_array, degree)

                            if x_smooth is not None and y_smooth is not None:
                                ax.plot(x_smooth, y_smooth,
                                        color=chart['color'],
                                        linestyle=chart['linestyle'],
                                        linewidth=float(chart['linewidth']),
                                        alpha=0.8,
                                        label=f"{chart['label']} (polynomial {degree} deg., {info})")
                            else:
                                # If approximation failed, show regular lines
                                ax.plot(x_array, y_array,
                                        color=chart['color'],
                                        linestyle='--',
                                        linewidth=float(chart['linewidth']),
                                        alpha=0.5,
                                        label=f"{chart['label']} (approximation failed)")

                        elif fit_type == 'regression':
                            # Linear regression
                            slope, intercept, r_value, p_value, std_err = stats.linregress(x_array, y_array)
                            x_line = np.array([min(x_array), max(x_array)])
                            y_line = slope * x_line + intercept
                            ax.plot(x_line, y_line,
                                    color=chart['color'],
                                    linestyle=chart['linestyle'],
                                    linewidth=float(chart['linewidth']),
                                    alpha=0.8,
                                    label=f"{chart['label']} (regression, R²={r_value ** 2:.4f})")

                except Exception as e:
                    print(f"Error processing file {chart['path']}: {e}")
                    snack_bar = ft.SnackBar(
                        ft.Row([ft.Text(f'Error: {e}', color=ft.colors.RED)],
                               alignment=ft.MainAxisAlignment.CENTER),
                    )
                    snack_bar.open = True
                    page.overlay.append(snack_bar)

            # Setup title and labels
            if title:
                ax.set_title(title, fontsize=14, pad=20)
            if x_label:
                ax.set_xlabel(x_label, fontsize=12)
            if y_label:
                ax.set_ylabel(y_label, fontsize=12)

            # Setup axis limits
            if x_min is not None and x_max is not None:
                ax.set_xlim(x_min, x_max)
            if y_min is not None and y_max is not None:
                ax.set_ylim(y_min, y_max)

            # Setup axis ticks
            if x_ticks:
                try:
                    ticks = [float(t.strip()) for t in x_ticks.split(',')]
                    ax.set_xticks(ticks)
                except:
                    pass

            if y_ticks:
                try:
                    ticks = [float(t.strip()) for t in y_ticks.split(',')]
                    ax.set_yticks(ticks)
                except:
                    pass

            # Setup grid
            if grid:
                ax.grid(True, alpha=0.3)
            if grid_minor:
                ax.grid(which='minor', linewidth=0.5, linestyle='--', alpha=0.3)
                ax.minorticks_on()

            # Setup legend
            if legend and chart_array:
                ax.legend(loc='best', fontsize=10)

            # apply_theme_to_plot(fig, ax, current_theme)
            plt.tight_layout()

            chart_container.content = MatplotlibChart(fig, expand=True)
            page.update()

        except Exception as e:
            print(f"Error building chart: {e}")
            snack_bar = ft.SnackBar(
                ft.Row([ft.Text(f'Error: {e}', color=ft.colors.RED)],
                       alignment=ft.MainAxisAlignment.CENTER),
            )
            snack_bar.open = True
            page.overlay.append(snack_bar)

    def update_chart_field():
        """Update the text field with the list of charts"""
        if not chart_array:
            chart_field.value = ''
            return

        result = []
        for i, chart in enumerate(chart_array, 1):
            file_name = os.path.basename(chart['path'])
            fit_type_display = {
                'line': 'line',
                'polyfit': f'polynomial {chart.get("polyfit_degree", 1)} deg.',
                'regression': 'regression'
            }.get(chart.get('fit_type', 'line'), 'line')
            result.append(f"{i}) '{chart['label']}' from '{file_name}' [{fit_type_display}]")

        chart_field.value = '\n'.join(result)
        page.update()

    def delete_chart_from_list(chart_text):
        """Delete chart by its text representation"""
        global chart_array, path_array, count_function

        # Extract chart name from button text
        parts = chart_text.split(' ')
        if parts:
            label_to_delete = parts[0]

            # Find and delete chart
            for i, chart in enumerate(chart_array):
                if chart['label'] == label_to_delete:
                    del chart_array[i]
                    break

            # Update path_array
            path_array = {chart['path'] for chart in chart_array}

            # Update display
            update_chart_field()

            # Update delete buttons
            delete_slot.clear()
            for chart in chart_array:
                btn = btn_delete(
                    f"{chart['label']} {os.path.basename(chart['path'])}",
                    ft.colors.RED,
                    ft.icons.DELETE_SWEEP,
                    on_delete_callback=delete_chart_from_list
                )
                delete_slot.push_element(btn)

            page.update()

    def toggle_theme():
        global current_theme
        if current_theme == 'dark':
            current_theme = 'light'
            page.theme_mode = ft.ThemeMode.LIGHT
        else:
            current_theme = 'dark'
            page.theme_mode = ft.ThemeMode.DARK
        page.update()
        # Redraw chart with new theme
        draw_chart(None)

    def navigate(index):
        page.clean()
        if index == 0:
            page.add(panel_data)
        elif index == 1:
            page.add(panel_setting)
        elif index == 2:
            page.add(panel_delete)
        # elif index == 3:
        #     # toggle_theme()
        #     pass
        page.update()

    def pick_result(e: ft.FilePickerResultEvent):
        if not e.files:
            snack_bar = ft.SnackBar(
                ft.Row(
                    [
                        ft.Text('File not selected!', color=ft.colors.RED),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
            )
            snack_bar.open = True
            page.overlay.append(snack_bar)
            page.update()
            return

        global path, count_function
        path = e.files[0].path
        path = os.path.normpath(path)

        try:
            with open(path, 'r', encoding='utf-8') as file:
                text_field.value = file.read()

            btn_select.text = os.path.basename(path)
            btn_save.disabled = False
            btn_add.disabled = False
            btn_close.disabled = False

            chart_label.value = f'Chart {count_function + 1}'
            chart_color.value = 'red'
            chart_point.value = '.'
            chart_linestyle.value = '-'
            chart_linewidth.value = '1'
            chart_fit_type.value = 'line'
            chart_polyfit_degree.value = '1'

        except Exception as e:
            snack_bar = ft.SnackBar(
                ft.Row([ft.Text(f'Error: {e}', color=ft.colors.RED)],
                       alignment=ft.MainAxisAlignment.CENTER),
            )
            snack_bar.open = True
            page.overlay.append(snack_bar)

        page.update()

    def save_file(e):
        global path
        try:
            with open(path, 'w', encoding='utf-8') as file:
                file.write(text_field.value)

            snack_bar = ft.SnackBar(
                ft.Row([ft.Text('File saved', color=ft.colors.GREEN)],
                       alignment=ft.MainAxisAlignment.CENTER),
            )
            snack_bar.open = True
            page.overlay.append(snack_bar)
        except Exception as e:
            snack_bar = ft.SnackBar(
                ft.Row([ft.Text(f'Error: {e}', color=ft.colors.RED)],
                       alignment=ft.MainAxisAlignment.CENTER),
            )
            snack_bar.open = True
            page.overlay.append(snack_bar)
        page.update()

    def close_file(e):
        global path
        try:
            if path:
                with open(path, 'w', encoding='utf-8') as file:
                    file.write(text_field.value)
        except:
            pass

        text_field.value = ''
        btn_select.text = 'Select file'
        btn_save.disabled = True
        btn_add.disabled = True
        btn_close.disabled = True

        page.update()

    def title_chart(e):
        global title
        title = title_field.value

    def x_label_chart(e):
        global x_label
        x_label = x_label_field.value

    def y_label_chart(e):
        global y_label
        y_label = y_label_field.value

    # New functions for axis settings
    def fig_width_change(e):
        global fig_width
        try:
            fig_width = float(fig_width_field.value)
        except:
            pass

    def fig_height_change(e):
        global fig_height
        try:
            fig_height = float(fig_height_field.value)
        except:
            pass

    def fig_dpi_change(e):
        global fig_dpi
        try:
            fig_dpi = int(fig_dpi_field.value)
        except:
            pass

    def x_min_change(e):
        global x_min
        try:
            val = x_min_field.value.strip()
            x_min = float(val) if val else None
        except:
            x_min = None

    def x_max_change(e):
        global x_max
        try:
            val = x_max_field.value.strip()
            x_max = float(val) if val else None
        except:
            x_max = None

    def y_min_change(e):
        global y_min
        try:
            val = y_min_field.value.strip()
            y_min = float(val) if val else None
        except:
            y_min = None

    def y_max_change(e):
        global y_max
        try:
            val = y_max_field.value.strip()
            y_max = float(val) if val else None
        except:
            y_max = None

    def x_ticks_change(e):
        global x_ticks
        x_ticks = x_ticks_field.value if x_ticks_field.value else None

    def y_ticks_change(e):
        global y_ticks
        y_ticks = y_ticks_field.value if y_ticks_field.value else None

    def fit_type_change(e):
        """Handler for fit type change"""
        if chart_fit_type.value == 'polyfit':
            chart_polyfit_degree.disabled = False
        else:
            chart_polyfit_degree.disabled = True
        page.update()

    def add_chart(e):
        global path, chart_array, path_array, count_function

        if not path:
            snack_bar = ft.SnackBar(
                ft.Row([ft.Text('Select a file first!', color=ft.colors.RED)],
                       alignment=ft.MainAxisAlignment.CENTER),
            )
            snack_bar.open = True
            page.overlay.append(snack_bar)
            page.update()
            return

        len_1 = len(path_array)
        path_array.add(path)
        len_2 = len(path_array)

        chart_data = {
            'path': path,
            'label': chart_label.value,
            'color': chart_color.value,
            'marker': chart_point.value,
            'linestyle': chart_linestyle.value,
            'linewidth': float(chart_linewidth.value),
            'fit_type': chart_fit_type.value,
            'polyfit_degree': int(chart_polyfit_degree.value) if chart_polyfit_degree.value.isdigit() else 1
        }

        if len_1 != len_2:
            chart_array.append(chart_data)
            count_function += 1
        else:
            for i in range(len(chart_array)):
                if chart_array[i]['path'] == path:
                    chart_array[i] = chart_data

        # Update display
        update_chart_field()

        # Update delete buttons
        delete_slot.clear()
        for chart in chart_array:
            btn = btn_delete(
                f"{chart['label']} {os.path.basename(chart['path'])}",
                ft.colors.RED,
                ft.icons.DELETE_SWEEP,
                on_delete_callback=delete_chart_from_list
            )
            delete_slot.push_element(btn)

        snack_bar = ft.SnackBar(
            ft.Row([ft.Text(f"Chart '{chart_label.value}' added", color=ft.colors.GREEN)],
                   alignment=ft.MainAxisAlignment.CENTER),
        )
        snack_bar.open = True
        page.overlay.append(snack_bar)
        page.update()

    def grid_checkbox_change(e):
        global grid
        grid = grid_checkbox.value
        grid_text.value = 'ON' if grid else 'OFF'
        page.update()

    def grid_minor_checkbox_change(e):
        global grid_minor
        grid_minor = grid_minor_checkbox.value
        grid_minor_text.value = 'ON' if grid_minor else 'OFF'
        page.update()

    def label_checkbox_change(e):
        global legend
        legend = legend_checkbox.value
        legend_text.value = 'ON' if legend else 'OFF'
        page.update()

    ####################################################################################################################
    # elements
    ####################################################################################################################

    # panel navigation
    rail = ft.NavigationRail(
        selected_index=0,
        label_type=ft.NavigationRailLabelType.ALL,
        min_width=70,
        min_extended_width=400,
        leading=ft.FloatingActionButton(icon=ft.icons.DRAW, disabled=False,
                                        on_click=draw_chart, tooltip="Draw chart"),
        group_alignment=-0.9,
        destinations=[
            ft.NavigationRailDestination(
                icon=ft.icons.BOOKMARK_BORDER,
                selected_icon=ft.icons.BOOKMARK,
                label="Data"
            ),
            ft.NavigationRailDestination(
                icon=ft.icons.SETTINGS_OUTLINED,
                selected_icon_content=ft.Icon(ft.icons.SETTINGS),
                label_content=ft.Text("Settings"),
            ),
            ft.NavigationRailDestination(
                icon=ft.icons.DELETE_OUTLINE,
                selected_icon_content=ft.Icon(ft.icons.DELETE),
                label_content=ft.Text("Manage"),
            ),
            # ft.NavigationRailDestination(
            #     icon=ft.icons.SUNNY,
            #     selected_icon_content=ft.Icon(ft.icons.NIGHTLIGHT),
            #     label_content=ft.Text("Theme"),
            # ),
        ],
        on_change=lambda e: navigate(e.control.selected_index)
    )

    # elements for panel data
    pick_dialog = ft.FilePicker(on_result=pick_result)
    page.overlay.append(pick_dialog)
    btn_select = ft.FilledButton(text='Select file', icon=ft.icons.UPLOAD_FILE,
                                 on_click=lambda _: pick_dialog.pick_files(allow_multiple=False))
    text_field = ft.TextField(label='File', width=500, multiline=True, border_color=ft.colors.WHITE, max_lines=10)
    chart_field = ft.TextField(label='Charts', width=500, multiline=True, border_color=ft.colors.WHITE, max_lines=5,
                               read_only=True, value='')
    btn_save = ft.FilledButton(text='Save file', on_click=save_file, disabled=True)
    btn_add = ft.FilledButton(text='Add chart', on_click=add_chart, disabled=True)
    btn_close = ft.FilledButton(text='Close file', on_click=close_file, disabled=True)

    chart_label = ft.TextField(label='Label', width=114, border_color=ft.colors.WHITE,
                               value=f'Chart {count_function + 1}')
    chart_color = ft.Dropdown(
        label='Color',
        width=70,
        options=[
            ft.dropdown.Option("red", "🔴"),
            ft.dropdown.Option("orange", "🟠"),
            ft.dropdown.Option("yellow", "🟡"),
            ft.dropdown.Option("green", "🟢"),
            ft.dropdown.Option("cyan", "🔵"),
            ft.dropdown.Option("blue", "💙"),
            ft.dropdown.Option("purple", "🟣"),
            ft.dropdown.Option("magenta", "🟣"),
            ft.dropdown.Option("black", "⚫"),
            ft.dropdown.Option("white", "⚪"),
        ],
        border_color=ft.colors.WHITE,
        value="red",
    )
    chart_point = ft.Dropdown(
        label='Marker',
        width=82,
        options=[
            ft.dropdown.Option(" ", "None"),
            ft.dropdown.Option(".", "."),
            ft.dropdown.Option("*", "*"),
            ft.dropdown.Option("o", "o"),
            ft.dropdown.Option("v", "3v"),
            ft.dropdown.Option("s", "4v"),
            ft.dropdown.Option("p", "5v"),
            ft.dropdown.Option("h", "6v"),
            ft.dropdown.Option("x", "x"),
        ],
        border_color=ft.colors.WHITE,
        value=".",
    )
    chart_linestyle = ft.Dropdown(
        label='Style',
        width=82,
        options=[
            ft.dropdown.Option("", " "),
            ft.dropdown.Option("-", "-"),
            ft.dropdown.Option("--", "--"),
            ft.dropdown.Option("-.", "-."),
            ft.dropdown.Option(":", ":"),
        ],
        border_color=ft.colors.WHITE,
        value="-"
    )
    chart_linewidth = ft.TextField(label='Width', width=82, border_color=ft.colors.WHITE, value='1')

    # New elements for fit type selection
    chart_fit_type = ft.Dropdown(
        label='Connection type',
        width=150,
        options=[
            ft.dropdown.Option("line", "line"),
            ft.dropdown.Option("polyfit", "polyfit"),
            ft.dropdown.Option("regression", "regression"),
        ],
        border_color=ft.colors.WHITE,
        value="line",
        on_change=fit_type_change
    )

    chart_polyfit_degree = ft.TextField(
        label='Polynomial degree',
        width=120,
        border_color=ft.colors.WHITE,
        value='1',
        disabled=True,
        hint_text="1-5"
    )

    # container with a chart
    chart_container = ft.Container(
        content=ft.Text("Chart"),
        margin=10,
        padding=10,
        border=ft.border.all(1, ft.colors.WHITE),
        alignment=ft.alignment.center,
        width=860,
        height=600,
        border_radius=10,
        ink=True,
    )

    # panel data
    panel_data = ft.Row(
        controls=[
            rail,
            ft.VerticalDivider(width=1),
            ft.Column(
                [
                    ft.Text('Data input', size=40),
                    ft.Text('Format: x y (numbers separated by space)', size=15, color=ft.colors.GREY),
                    btn_select,
                    text_field,
                    ft.Row(
                        [
                            chart_label,
                            chart_color,
                            chart_point,
                            chart_linestyle,
                            chart_linewidth,
                        ]
                    ),
                    ft.Row(
                        [
                            chart_fit_type,
                            chart_polyfit_degree,
                        ]
                    ),
                    ft.Row(
                        [
                            btn_save,
                            btn_add,
                            btn_close,
                        ]
                    ),
                    chart_field,
                ],
                spacing=15,
                width=500
            ),
            chart_container,
        ],
        expand=True,
    )

    # elements for panel settings
    title_field = ft.TextField(label='Title', on_change=title_chart, border_color=ft.colors.WHITE, width=500,
                               multiline=True)
    x_label_field = ft.TextField(label='X axis label', on_change=x_label_chart, border_color=ft.colors.WHITE,
                                 width=500, multiline=True)
    y_label_field = ft.TextField(label='Y axis label', on_change=y_label_chart, border_color=ft.colors.WHITE,
                                 width=500, multiline=True)

    # Image size settings
    fig_width_field = ft.TextField(label='Width (inches)', width=120, border_color=ft.colors.WHITE,
                                   value='8', on_change=fig_width_change)
    fig_height_field = ft.TextField(label='Height (inches)', width=120, border_color=ft.colors.WHITE,
                                    value='5', on_change=fig_height_change)
    fig_dpi_field = ft.TextField(label='DPI', width=100, border_color=ft.colors.WHITE,
                                 value='100', on_change=fig_dpi_change)

    # Axis limits settings
    x_min_field = ft.TextField(label='X min', width=100, border_color=ft.colors.WHITE,
                               hint_text='auto', on_change=x_min_change)
    x_max_field = ft.TextField(label='X max', width=100, border_color=ft.colors.WHITE,
                               hint_text='auto', on_change=x_max_change)
    y_min_field = ft.TextField(label='Y min', width=100, border_color=ft.colors.WHITE,
                               hint_text='auto', on_change=y_min_change)
    y_max_field = ft.TextField(label='Y max', width=100, border_color=ft.colors.WHITE,
                               hint_text='auto', on_change=y_max_change)

    # Ticks settings
    x_ticks_field = ft.TextField(label='X ticks (comma separated)', width=250, border_color=ft.colors.WHITE,
                                 hint_text='0, 1, 2, 3', on_change=x_ticks_change)
    y_ticks_field = ft.TextField(label='Y ticks (comma separated)', width=250, border_color=ft.colors.WHITE,
                                 hint_text='0, 1, 2, 3', on_change=y_ticks_change)

    grid_checkbox = ft.Checkbox(label='Grid: ', shape=ft.RoundedRectangleBorder(radius=7),
                                label_position=ft.LabelPosition.LEFT, on_change=grid_checkbox_change)
    grid_text = ft.Text(value='OFF', size=14)
    grid_minor_checkbox = ft.Checkbox(label='Minor grid: ', shape=ft.RoundedRectangleBorder(radius=7),
                                      label_position=ft.LabelPosition.LEFT, on_change=grid_minor_checkbox_change)
    grid_minor_text = ft.Text(value='OFF', size=14)
    legend_checkbox = ft.Checkbox(label='Legend: ', shape=ft.RoundedRectangleBorder(radius=7),
                                  label_position=ft.LabelPosition.LEFT, on_change=label_checkbox_change)
    legend_text = ft.Text(value='OFF', size=14)

    # panel settings
    panel_setting = ft.Row(
        [
            rail,
            ft.VerticalDivider(width=1),
            ft.Column(
                [
                    ft.Text('Chart settings', size=40),
                    title_field,
                    x_label_field,
                    y_label_field,
                    ft.Divider(height=10),
                    ft.Text('Image size', size=20, weight=ft.FontWeight.BOLD),
                    ft.Row([fig_width_field, fig_height_field, fig_dpi_field]),
                    ft.Divider(height=10),
                    ft.Text('Axis limits', size=20, weight=ft.FontWeight.BOLD),
                    ft.Row([x_min_field, x_max_field]),
                    ft.Row([y_min_field, y_max_field]),
                    ft.Divider(height=10),
                    ft.Text('Axis ticks', size=20, weight=ft.FontWeight.BOLD),
                    x_ticks_field,
                    y_ticks_field,
                    ft.Divider(height=10),
                    ft.Row([grid_checkbox, grid_text]),
                    ft.Row([grid_minor_checkbox, grid_minor_text]),
                    ft.Row([legend_checkbox, legend_text]),
                ],
                spacing=15,
                scroll=ft.ScrollMode.AUTO,
                width=500,
                height=650
            ),
            chart_container,
        ],
        expand=True,
    )

    # panel delete
    panel_delete = ft.Row(
        [
            rail,
            ft.VerticalDivider(width=1),
            ft.Column(
                [
                    ft.Text('Manage charts', size=40),
                    ft.Text('Chart list:', size=16),
                    chart_field,
                    ft.Divider(height=10),
                    ft.Text('Delete chart:', size=16),
                    delete_slot,
                ],
                spacing=15,
                width=500
            ),
            chart_container,
        ],
        expand=True,
    )
    page.add(panel_data)


if __name__ == '__main__':
    ft.app(target=main)