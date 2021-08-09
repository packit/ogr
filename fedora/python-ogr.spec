%global srcname ogr

Name:           python-%{srcname}
Version:        0.28.0
Release:        1%{?dist}
Summary:        One API for multiple git forges

License:        MIT
URL:            https://github.com/packit/ogr
Source0:        %{pypi_source}
BuildArch:      noarch

BuildRequires:  python3-devel
BuildRequires:  python3dist(setuptools)
BuildRequires:  python3dist(setuptools-scm)
BuildRequires:  python3dist(setuptools-scm-git-archive)

%description
One Git library to Rule!

%package -n     python3-%{srcname}
Summary:        %{summary}

# https://docs.fedoraproject.org/en-US/packaging-guidelines/Python/#_provides
%if 0%{?fedora} < 33
%{?python_provide:%python_provide python3-%{srcname}}
%endif

%description -n python3-%{srcname}
One Git library to Rule!


%prep
%autosetup -n %{srcname}-%{version}
# Remove bundled egg-info
rm -rf %{srcname}.egg-info


%build
%py3_build


%install
%py3_install


%files -n python3-%{srcname}
%license LICENSE
%doc README.md
%{python3_sitelib}/%{srcname}
%{python3_sitelib}/%{srcname}-%{version}-py%{python3_version}.egg-info


%changelog
* Mon Aug 09 2021 Matej Focko <mfocko@redhat.com> - 0.28.0-1
- New upstream release 0.28.0

* Thu Jul 15 2021 Jiri Popelka <jpopelka@redhat.com> - 0.27.0-1
- New upstream release 0.27.0

* Fri Jun 11 2021 Tomas Tomecek <ttomecek@redhat.com> - 0.26.0-1
- New upstream release 0.26.0

* Tue Jun 01 2021 Laura Barcziova <lbarczio@redhat.com> - 0.25.0-1
- New upstream release 0.25.0

* Tue Apr 27 2021 Matej Mužila <mmuzila@redhat.com> - 0.24.1-1
- New upstream release 0.24.1

* Fri Apr 23 2021 Matej Mužila <mmuzila@redhat.com> - 0.24.0-1
- New upstream release 0.24.0

* Thu Mar 18 2021 Jiri Popelka <jpopelka@redhat.com> - 0.23.0-1
- New upstream release 0.23.0

* Fri Feb 19 2021 Matej Focko <mfocko@redhat.com> - 0.21.0-1
- New upstream release 0.21.0

* Thu Feb 04 2021 Matej Focko <mfocko@redhat.com> - 0.20.0-1
- New upstream release 0.20.0

* Thu Jan  7 10:52:27 CET 2021 Tomas Tomecek <ttomecek@redhat.com> - 0.19.0-1
- New upstream release 0.19.0

* Wed Dec 09 2020 Jan Sakalos <sakalosj@gmail.com> - 0.18.1-1
- New upstream release 0.18.1

* Tue Oct 27 2020 Jiri Popelka <jpopelka@redhat.com> - 0.18.0-1
- New upstream release 0.18.0

* Wed Sep 30 2020 Matej Focko <mfocko@redhat.com> - 0.16.0-1
- New upstream release 0.16.0

* Wed Sep 16 2020 Tomas Tomecek <ttomecek@redhat.com> - 0.15.0-1
- New upstream release 0.15.0

* Tue Sep 01 2020 Dominika Hodovska <dhodovsk@redhat.com> - 0.14.0-1
- New upstream release 0.14.0

* Wed Aug 19 2020 Jan Sakalos <sakalosj@gmail.com> - 0.13.1-1
- New upstream release 0.13.1

* Wed Aug 05 2020 Jan Sakalos <sakalosj@gmail.com> - 0.13.0-1
- New upstream release 0.13.0

* Thu Jul 09 2020 Jiri Popelka <jpopelka@redhat.com> - 0.12.2-1
- New upstream release 0.12.2

* Wed May 27 2020 Dominika Hodovska <dhodovsk@redhat.com> - 0.12.1-1
- New upstream release 0.12.1

* Wed May 06 2020 Frantisek Lachman <flachman@redhat.com> - 0.12.0-1
- New upstream release 0.12.0

* Fri Apr 17 2020 Frantisek Lachman <flachman@redhat.com> - 0.11.2-1
- New upstream release 0.11.2

* Wed Apr 01 2020 Jan Sakalos <sakalosj@gmail.com> - 0.11.1-1
- patch release: 0.11.1

* Sat Mar 07 2020 Jiri Popelka <jpopelka@redhat.com> - 0.11.0-1
- New upstream release 0.11.0

* Tue Jan 28 2020 Frantisek Lachman <flachman@redhat.com> - 0.10.0-1
- New upstream release 0.10.0

* Wed Dec 04 2019 Frantisek Lachman <flachman@redhat.com> - 0.9.0-1
- New upstream release 0.9.0

* Mon Sep 30 2019 Frantisek Lachman <flachman@redhat.com> - 0.8.0-1
- New upstream release 0.8.0

* Wed Sep 11 2019 Frantisek Lachman <flachman@redhat.com> - 0.7.0-1
- New upstream release 0.7.0

* Tue Jul 23 2019 Frantisek Lachman <flachman@redhat.com> - 0.6.0-1
- New upstream release 0.6.0

* Fri Jun 28 2019 Frantisek Lachman <flachman@redhat.com> - 0.5.0-1
- New upstream release: 0.5.0

* Tue Jun 11 2019 Jiri Popelka <jpopelka@redhat.com> - 0.4.0-1
- New upstream release: 0.4.0

* Tue May 14 2019 Jiri Popelka <jpopelka@redhat.com> - 0.3.1-1
- patch release: 0.3.1

* Mon May 13 2019 Jiri Popelka <jpopelka@redhat.com> - 0.3.0-1
- New upstream release: 0.3.0

* Wed Mar 27 2019 Tomas Tomecek <ttomecek@redhat.com> - 0.2.0-1
- New upstream release: 0.2.0

* Mon Mar 18 2019 Tomas Tomecek <ttomecek@redhat.com> - 0.1.0-1
- New upstream release: 0.1.0

* Thu Feb 28 2019 Frantisek Lachman <flachman@redhat.com> - 0.0.3-1
- New upstream release 0.0.3

* Tue Feb 26 2019 Tomas Tomecek <ttomecek@redhat.com> - 0.0.2-1
- Initial package.
