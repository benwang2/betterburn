import discord


class LinkView(discord.ui.View):
    def __init__(self, link_url):
        super().__init__(timeout=60)  # The view is active for 60 seconds
        self.add_item(
            discord.ui.Button(
                label="Authenticate", url=link_url, style=discord.ButtonStyle.blurple
            )
        )

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.danger)
    async def end_interaction(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        embed = discord.Embed(
            title="Linking session ended",
            description="You have canceled the linking process. If you wish to try again, use the `/link` command.",
            color=discord.Color.red(),
        )
        await interaction.response.edit_message(embed=embed, view=None)
