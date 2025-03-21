from datetime import date, datetime
import matplotlib.pyplot as plt
import base64
import io
import numpy as np

class PlotHandler:
    
    def __init__(self):
        pass

    # region Plot

    def create_activity_plot(activity_times):
        """Generera en stående stapelgraf med unika färger för varje mål."""
        activity_names = [activity[0] for activity in activity_times]
        total_times = [activity[1] for activity in activity_times]

        # Färger för varje stapel, genereras automatiskt för att vara unika
        colors = plt.cm.get_cmap('tab20', len(activity_names))(range(len(activity_names)))
        plt.figure(figsize=(10, 8), facecolor='none', edgecolor='k', )
        plt.bar(activity_names, total_times, color=colors)  # Stående staplar
        plt.ylabel('Total Tid (min)', fontsize=10)
        plt.xlabel('Aktivitet', fontsize=10)
        plt.xticks(rotation=0, ha='center', fontsize=14)
        plt.yticks(rotation=0, ha='right', fontsize=14)
        img = io.BytesIO()
        plt.savefig(img, format='png')
        img.seek(0)
        # Konvertera bilden till base64 för att inkludera den i HTML
        plot_url = base64.b64encode(img.getvalue()).decode('utf8')
        plt.close()
        return plot_url

    def create_grouped_bar_plot(data_dicts, labels_list=None, title="Summering", ylabel="Tid (min)"):
        # 1. Samla alla unika labels från alla dictionaries
        all_labels = set()
        for d in data_dicts:
            all_labels.update(d.keys())
        all_labels = sorted(all_labels)  # Sorterade för snyggare presentation

        # 2. Extrahera värden, säkerställ att varje dataset har värden för alla labels (fyll 0 annars)
        all_values = []
        for d in data_dicts:
            values = [d.get(label, 0) for label in all_labels]
            all_values.append(values)

        # 3. Gör snygg formatering om labels är datum
        all_labels = [label.strftime('%a %d-%m') if isinstance(label, (datetime, date)) else label for label in all_labels]

        # 4. Plot inställningar
        x = np.arange(len(all_labels))  # x-axelns positioner
        width = 0.8 / len(data_dicts)  # Bredd anpassad för antal grupper (max bredd 0.8)

        plt.figure(figsize=(12, 6))
        colors = plt.cm.get_cmap('tab10', len(data_dicts))  # Unika färger för varje dataset

        # 5. Skapa staplar för varje data_dict
        for idx, values in enumerate(all_values):
            offset = (idx - (len(data_dicts) - 1) / 2) * width  # Placera bredvid varandra
            label = labels_list[idx] if labels_list and idx < len(labels_list) else f"Data {idx+1}"
            bars = plt.bar(x + offset, values, width=width, label=label, color=colors(idx), alpha=0.8)

            # Lägg siffror ovanpå varje stapel
            for bar in bars:
                height = bar.get_height()
                if height > 0:
                    plt.text(bar.get_x() + bar.get_width() / 2.0, height, f'{int(height)}',
                            ha='center', va='bottom', fontsize=10)

        # 6. Layout och stil
        plt.title(title, fontsize=16)
        plt.ylabel(ylabel, fontsize=14)
        plt.xticks(x, all_labels, rotation=45, ha='right', fontsize=12)
        plt.yticks(fontsize=12)
        plt.legend(fontsize=12)
        plt.grid(axis='y', linestyle='--', alpha=0.7)
        plt.tight_layout()

        # 7. Exportera som base64 för HTML
        img = io.BytesIO()
        plt.savefig(img, format='png')
        img.seek(0)
        plt.close()

        return base64.b64encode(img.getvalue()).decode('utf8')

    def create_bar_plot(data_dict, title="Summering", ylabel="Tid (min)"):
        """
        Skapar en stapelgraf från en dictionary med {'label': value}.
        Returnerar grafen som en base64-sträng (för att använda i templates).
        """
        labels = list(data_dict.keys())  # Exempelvis dagar, mål eller aktiviteter
        values = list(data_dict.values())  # Tiden för varje

        # Snygg formatering för datum (om labels är datumobjekt)
        labels = [label.strftime('%a %d-%m') if isinstance(label, (datetime, date)) else label for label in labels]

        plt.figure(figsize=(10, 6))
        bars = plt.bar(labels, values, color='skyblue', alpha=0.7)

        # Lägg etiketter på staplarna
        for bar in bars:
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width() / 2.0, height, f'{int(height)}', ha='center', va='bottom', fontsize=10)

        plt.title(title, fontsize=16)
        plt.ylabel(ylabel, fontsize=14)
        plt.xticks(rotation=45, ha='right', fontsize=12)
        plt.yticks(fontsize=12)
        plt.tight_layout()
        plt.grid(axis='y', linestyle='--', alpha=0.7)

        # Exportera som base64
        img = io.BytesIO()
        plt.savefig(img, format='png')
        img.seek(0)
        plt.close()
        return base64.b64encode(img.getvalue()).decode('utf8')


    def create_week_comparison_plot(this_week_scores, last_week_scores):
        days = ['Mån', 'Tis', 'Ons', 'Tors', 'Fre', 'Lör', 'Sön']
        x = range(len(days))

        # Konvertera datan till en form som passar grafer
        this_week_data = {score.Date.weekday(): score.total_points for score in this_week_scores}
        last_week_data = {score.Date.weekday(): score.total_points for score in last_week_scores}

        this_week = [this_week_data.get(i, 0) for i in range(7)]
        last_week = [last_week_data.get(i, 0) for i in range(7)]

        plt.figure(figsize=(10, 6))
        plt.bar(x, last_week, alpha=0.2, label="Föregående vecka", color="blue",)
        plt.bar(x, this_week, alpha=0.6, label="Aktuell vecka", color="orange")
        plt.xticks(x, days, fontsize=14)
    #    plt.ylabel("Score")
        plt.ylim(15, 350)  # Sätter y-axeln från 15 till 350
        plt.yticks(range(0, 360, 30), fontsize=14)
        plt.legend(fontsize=14)
        plt.tight_layout(pad=2.0)
        plt.grid(color='lightgray', linestyle='--', linewidth=0.5)  # Ställ in rutnätets stil och färg

        img = io.BytesIO()
        plt.savefig(img, format='png')
        img.seek(0)
        plt.close()
        return base64.b64encode(img.getvalue()).decode('utf8')

    # endregion