from django import forms
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from django.contrib.auth.models import User

class RegistroUsuarioForm(UserCreationForm):
    email = forms.EmailField(required=True, help_text='Requerido. Ingresa un email válido.')
    first_name = forms.CharField(max_length=30, required=True, help_text='Requerido. Ingresa tu nombre.')
    last_name = forms.CharField(max_length=30, required=True, help_text='Requerido. Ingresa tu apellido.')
    
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Personalizar mensajes de ayuda
        self.fields['username'].help_text = 'Requerido. 150 caracteres o menos. Solo letras, dígitos y @/./+/-/_'
        self.fields['password1'].help_text = '''
        <ul>
            <li>Tu contraseña no puede ser muy similar a tu información personal.</li>
            <li>Tu contraseña debe contener al menos 8 caracteres.</li>
            <li>Tu contraseña no puede ser una contraseña comúnmente utilizada.</li>
            <li>Tu contraseña no puede ser completamente numérica.</li>
        </ul>
        '''
        self.fields['password2'].help_text = 'Ingresa la misma contraseña que antes, para verificación.'
        
        # Personalizar etiquetas
        self.fields['username'].label = 'Nombre de usuario'
        self.fields['first_name'].label = 'Nombre'
        self.fields['last_name'].label = 'Apellido'
        self.fields['email'].label = 'Correo electrónico'
        self.fields['password1'].label = 'Contraseña'
        self.fields['password2'].label = 'Confirmar contraseña'
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('Este correo electrónico ya está registrado.')
        return email
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        if commit:
            user.save()
        return user

class CambioPasswordForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Personalizar etiquetas
        self.fields['old_password'].label = 'Contraseña actual'
        self.fields['new_password1'].label = 'Nueva contraseña'
        self.fields['new_password2'].label = 'Confirmar nueva contraseña'
        
        # Personalizar mensajes de ayuda
        self.fields['new_password1'].help_text = '''
        <ul>
            <li>Tu contraseña no puede ser muy similar a tu información personal.</li>
            <li>Tu contraseña debe contener al menos 8 caracteres.</li>
            <li>Tu contraseña no puede ser una contraseña comúnmente utilizada.</li>
            <li>Tu contraseña no puede ser completamente numérica.</li>
        </ul>
        '''
        self.fields['new_password2'].help_text = 'Ingresa la misma contraseña que antes, para verificación.' 